import numpy as np
from mpi4py import MPI
import copy
import random

from genetic.evaluator import calculate_fitness
from genetic.operators import tournament_selection, crossover, mutate

STAGNATION_NUM = 30


def evaluate_population_parallel(population, config_data, comm):
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
    else:
        return None


def run_evolution_parallel(
    population,
    config_data,
    num_generations,
    population_size,
    tournament_size,
    crossover_prob,
    mutation_prob,
    elite_fraction=0.02,
):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    best_fitness = float('-inf')
    stagnation_counter = 0
    early_stopping_triggered = False

    if rank == 0:
        print("Starting parallel evolution...")

    for generation in range(num_generations):
        population = evaluate_population_parallel(population, config_data, comm)

        if rank == 0:
            population.sort(key=lambda ind: ind.fitness, reverse=True)
            elites = population[:max(1, int(elite_fraction * population_size))]

            if population[0].fitness > best_fitness:
                best_fitness = population[0].fitness
                stagnation_counter = 0
            else:
                stagnation_counter += 1

            avg_fitness = sum(ind.fitness for ind in population) / len(population)
            print(f"Generation {generation + 1}: avg = {avg_fitness:.4f}, best = {population[0].fitness:.4f}")

            if stagnation_counter >= STAGNATION_NUM:
                early_stopping_triggered = True
                print(f"Early stopping at generation {generation + 1} due to stagnation.")

        early_stopping_triggered = comm.bcast(early_stopping_triggered, root=0)
        if early_stopping_triggered:
            break

        if rank != 0:
            continue

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

            mutate(child1, mutation_prob, config_data['building_constraints'])
            mutate(child2, mutation_prob, config_data['building_constraints'])

            next_population.append(child1)
            if len(next_population) < population_size:
                next_population.append(child2)

        population = next_population

    population = evaluate_population_parallel(population, config_data, comm)
    comm.Barrier()
    if rank == 0:
        print("Evolution finished.")
        return population
    else:
        return None
