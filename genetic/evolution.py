import copy
import random

from genetic.evaluator import calculate_fitness
from genetic.operators import tournament_selection, crossover, mutate


def evaluate_population(population, config_data):
    for individual in population:
        individual.fitness = calculate_fitness(individual, config_data)


def run_evolution(
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
    print("Starting evolution...")

    best_fitness = float('-inf')
    stagnation_counter = 0

    for generation in range(num_generations):
        evaluate_population(population, config_data)

        population.sort(key=lambda ind: ind.fitness, reverse=True)
        elites = population[:max(1, int(elite_fraction * population_size))]

        if population[0].fitness > best_fitness:
            best_fitness = population[0].fitness
            stagnation_counter = 0
        else:
            stagnation_counter += 1

        avg_fitness = sum(ind.fitness for ind in population) / len(population)
        print(f"Generation {generation + 1}: avg = {avg_fitness:.4f}, best = {population[0].fitness:.4f}")

        # Early stopping
        if stagnation_counter >= int(num_generations * early_stopping_rounds_fraction):
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

    print("Evolution finished.")

    evaluate_population(population, config_data)
    return population
