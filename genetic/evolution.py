import copy
import random

from genetic.evaluator import calculate_fitness
from genetic.operators import tournament_selection, crossover, mutate


def run_evolution(population, config_data, num_generations, population_size, tournament_size, crossover_prob, mutation_prob):
    """
    Main function to run the genetic algorithm optimization.
    """

    print("Starting evolution...")

    for generation in range(num_generations):
        for individual in population:
            individual.fitness = calculate_fitness(individual, config_data)

        best_individual = max(population, key=lambda ind: individual.fitness)
        print(f"Generacja:{generation + 1} najlepszy osobnik: {best_individual}")

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
                child1, child2 = parent1, parent2

            mutate(child1, mutation_prob, config_data)
            mutate(child2, mutation_prob, config_data)

            next_population.append(child1)
            if len(next_population) < population_size:
                next_population.append(child2)
        population = next_population

    print('Evolution finished.')

    for individual in population:
        individual.fitness = calculate_fitness(individual, config_data)
    return population
