from mpi4py import MPI
import copy
import random

from genetic.evaluator import calculate_fitness
from genetic.operators import tournament_selection, crossover, mutate

def evaluate_population_parallel(population, config_data, comm):
    rank = comm.Get_rank()
    size = comm.Get_size()

    chunk_size = len(population) // size
    extra = len(population) % size

    if rank < extra:
        start = rank * (chunk_size + 1)
        end = start + chunk_size + 1
    else:
        start = rank * chunk_size + extra
        end = start + chunk_size

    local_chunk = population[start:end]

    for individual in local_chunk:
        individual.fitness = calculate_fitness(individual, config_data)

    all_chunks = comm.allgather(local_chunk)

    new_population = [ind for chunk in all_chunks for ind in chunk]

    return new_population


def run_evolution_parallel(
    population,
    config_data,
    num_generations,
    population_size,
    tournament_size,
    crossover_prob,
    mutation_prob,
    elite_fraction=0.02,
    early_stopping_rounds_fraction=0.15
):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        print("Starting parallel evolution...")

    best_fitness = float('-inf')
    stagnation_counter = 0

    for generation in range(num_generations):
        population = evaluate_population_parallel(population, config_data, comm)

        population.sort(key=lambda ind: ind.fitness, reverse=True)
        elites = population[:max(1, int(elite_fraction * population_size))]

        if rank == 0:
            if population[0].fitness > best_fitness:
                best_fitness = population[0].fitness
                stagnation_counter = 0
            else:
                stagnation_counter += 1

            avg_fitness = sum(ind.fitness for ind in population) / len(population)
            print(f"Generation {generation + 1}: avg = {avg_fitness:.4f}, best = {population[0].fitness:.4f}")

        # Broadcast stagnation counter (early stopping logic)
        stagnation_counter = comm.bcast(stagnation_counter if rank == 0 else None, root=0)
        best_fitness = comm.bcast(best_fitness if rank == 0 else None, root=0)

        if stagnation_counter >= int(num_generations * early_stopping_rounds_fraction):
            if rank == 0:
                print(f"Early stopping at generation {generation + 1} due to stagnation.")
            break

        # Adapt mutation probability
        curr_mutation_prob = mutation_prob * (1 - generation / num_generations)

        # Create new generation
        next_population = [copy.deepcopy(ind) for ind in elites]

        while len(next_population) < population_size:
            parent1 = tournament_selection(population, tournament_size)
            parent2 = tournament_selection(population, tournament_size)

            attempts = 0
            while parent1 is parent2 and attempts < 5:
                parent2 = tournament_selection(population, tournament_size)
                attempts += 1

            if random.random() < crossover_prob:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1 = copy.deepcopy(parent1)
                child2 = copy.deepcopy(parent2)

            mutate(child1, curr_mutation_prob, config_data['building_constraints'])
            mutate(child2, curr_mutation_prob, config_data['building_constraints'])

            next_population.append(child1)
            if len(next_population) < population_size:
                next_population.append(child2)

        population = next_population

    if rank == 0:
        print("Evolution finished.")

    # Final evaluation before return
    population = evaluate_population_parallel(population, config_data, comm)
    return population
