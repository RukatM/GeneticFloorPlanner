import copy
import random
from mpi4py import MPI
from genetic.evaluator import calculate_fitness
from genetic.operators import tournament_selection, crossover, mutate


def evaluate_population_parallel(population, config_data):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        chunks = [population[i::size] for i in range(size)]
    else:
        chunks = None

    local_chunk = comm.scatter(chunks, root=0)

    for individual in local_chunk:
        individual.fitness = calculate_fitness(individual, config_data)

    gathered_chunks = comm.gather(local_chunk, root=0)

    if rank == 0:
        return [ind for chunk in gathered_chunks for ind in chunk]
    else:
        return None

def run_evolution_parallel(population, config_data, num_generations, population_size, tournament_size, crossover_prob, mutation_prob):
    """
    Main function to run the genetic algorithm optimization with MPI-based fitness evaluation.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    if rank == 0:
        print("Starting evolution...")

    for generation in range(num_generations):
        population = evaluate_population_parallel(population, config_data)

        if rank == 0:
            best_individual = max(population, key=lambda ind: ind.fitness)
            average_fitness = sum(ind.fitness for ind in population) / len(population)
            print(f"Generation: {generation + 1}, average fitness: {average_fitness:.2f}, best fitness: {best_individual.fitness:.2f}")

            next_population = [copy.deepcopy(best_individual)]

            while len(next_population) < population_size:
                parent1 = tournament_selection(population, tournament_size)
                parent2 = tournament_selection(population, tournament_size)

                attempts = 0
                while parent1 is parent2 and attempts < 10:
                    parent2 = tournament_selection(population, tournament_size)
                    attempts += 1

                if random.random() < crossover_prob:
                    child1, child2 = crossover(parent1, parent2)
                else:
                    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)

                mutate(child1, mutation_prob, config_data['building_constraints'])
                mutate(child2, mutation_prob, config_data['building_constraints'])

                next_population.append(child1)
                if len(next_population) < population_size:
                    next_population.append(child2)
        else:
            next_population = None

        population = comm.bcast(next_population, root=0)

    if rank == 0:
        print('Evolution finished.')

    population = evaluate_population_parallel(population, config_data)

    return population if rank == 0 else None
