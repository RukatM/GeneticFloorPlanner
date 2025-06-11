import numpy as np
import copy
import random

from genetic.evaluator import calculate_fitness
from genetic.operators import tournament_selection, crossover, mutate

STAGNATION_NUM = 50


def evaluate_population_parallel(population, config_data, comm):
    """
    Evaluates fitness of the population in parallel using MPI.
    """

    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        data = np.array_split(population, size)
    else:
        data = None

    local_chunk = comm.scatter(data, root=0)

    for individual in local_chunk:
        individual.fitness = calculate_fitness(individual, config_data)

    gathered_chunks = comm.gather(local_chunk, root=0)

    if rank == 0:
        return [individual for chunk in gathered_chunks for individual in chunk]
    return None


def generate_next_population_parallel(
    global_population,
    config_data,
    population_size,
    tournament_size,
    crossover_prob,
    mutation_prob,
    elite_fraction,
    comm
):
    """
    Generates the next population using selection, crossover, and mutation in parallel.
    """

    rank = comm.Get_rank()
    size = comm.Get_size()

    if rank == 0:
        global_population.sort(key=lambda ind: ind.fitness, reverse=True)
        num_elites = max(1, int(elite_fraction * population_size))
        elites = [copy.deepcopy(ind) for ind in global_population[:num_elites]]

        indices = np.random.permutation(len(global_population))
        buckets = [[] for _ in range(size)]
        for i, idx in enumerate(indices):
            buckets[i % size].append(global_population[idx])
        population_split = buckets
    else:
        elites = None
        population_split = None

    local_population = list(comm.scatter(population_split, root=0))
    elites = comm.bcast(elites, root=0)

    next_population = []
    while len(next_population) < population_size // size:
        parent1 = tournament_selection(local_population, tournament_size)
        parent2 = tournament_selection(local_population, tournament_size)

        if random.random() < crossover_prob:
            child1, child2 = crossover(parent1, parent2)
        else:
            child1 = copy.copy(parent1)
            child2 = copy.copy(parent2)

        mutate(child1, mutation_prob, config_data['building_constraints'])
        mutate(child2, mutation_prob, config_data['building_constraints'])

        next_population.append(child1)
        if len(next_population) < population_size // size:
            next_population.append(child2)

    gathered_population = comm.gather(next_population, root=0)

    if rank == 0:
        combined = [ind for sublist in gathered_population for ind in sublist]
        remaining_slots = population_size - len(elites)
        return elites + combined[:remaining_slots]
    return None


def run_evolution_parallel(
    population,
    config_data,
    num_generations,
    population_size,
    tournament_size,
    crossover_prob,
    mutation_prob,
    comm,
    elite_fraction=0.02,
    debug = False
):
    """
    Runs the full evolutionary loop in parallel.
    """

    rank = comm.Get_rank()
    random.seed(42 + rank)

    best_fitness = float('-inf')
    stagnation_counter = 0
    early_stopping_triggered = False

    hall_of_fame = []

    population = comm.bcast(population, root=0)

    if rank == 0 and debug:
        print("Starting parallel evolution...")

    for generation in range(num_generations):
        population = evaluate_population_parallel(population, config_data, comm)

        if rank == 0:
            population.sort(key=lambda ind: ind.fitness, reverse=True)
            hall_of_fame.append(copy.deepcopy(population[0]))
            current_best = population[0].fitness
            avg_fitness = sum(ind.fitness for ind in population) / len(population)

            if current_best > best_fitness:
                best_fitness = current_best
                stagnation_counter = 0
            else:
                stagnation_counter += 1

            if debug:
                print(f"Generation {generation + 1}: avg = {avg_fitness:.4f}, best = {current_best:.4f}")

            if stagnation_counter >= STAGNATION_NUM:
                print(f"Early stopping at generation {generation + 1} due to stagnation.")
                early_stopping_triggered = True

        early_stopping_triggered = comm.bcast(early_stopping_triggered, root=0)
        if early_stopping_triggered:
            break

        population = generate_next_population_parallel(
            population,
            config_data,
            population_size,
            tournament_size,
            crossover_prob,
            mutation_prob,
            elite_fraction,
            comm
        )

        population = comm.bcast(population, root=0)

    population = evaluate_population_parallel(population, config_data, comm)
    comm.Barrier()

    if rank == 0:
        print("Evolution finished.")
        hall_of_fame.append(copy.deepcopy(population[0]))
        return population, hall_of_fame

    return None, None
