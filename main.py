import sys
import random
import copy
from inout.parser import parse_input_file
from genetic.operators import initialize_population,tournament_selection,crossover,mutate
from genetic.evaluator import calculate_fitness
from visualization.gui import preview


def run_optimization(num_generations, population_size, tournament_size, crossover_prob, mutation_prob):
    """
    Main function to run the genetic algorithm optimization.
    """
    
    input_filepath = "data/building_example.json"
    config_data = parse_input_file(input_filepath)

    if not config_data:
        print("Error: Could not load configuration data. Exiting.")
        sys.exit(1) 

    print("Configuration loaded successfully")

    print("Initializing population")
    population = initialize_population(config_data, population_size)

    if not population:
        print("Population initialisation failed")
        sys.exit(2) 

    else:
        print("Population succefully initialised")

        for generation in range(num_generations):
            for individual in population:
                individual.fitness = calculate_fitness(individual,config_data)

            best_individual = max(population,key = lambda ind : individual.fitness)
            print(f"Generacja:{generation + 1} najlepszy osobnik: {best_individual}")

            next_population = [copy.deepcopy(best_individual)]

            while len(next_population) < population_size:
                parent1 = tournament_selection(population,tournament_size)
                parent2 = tournament_selection(population,tournament_size)

                attempts= 0
                while parent1 is parent2 and attempts < 10:
                    parent2 = tournament_selection(population,tournament_size)
                    attempts += 1

                if random.random() < crossover_prob:
                    child1, child2 = crossover(parent1,parent2)
                else:
                    child1,child2 = parent1,parent2

                mutate(child1, mutation_prob, config_data)
                mutate(child2, mutation_prob, config_data)

                next_population.append(child1)
                if len(next_population) < population_size:
                    next_population.append(child2)
            population = next_population

    best_individual = max(population, key=lambda ind: individual.fitness)
    preview(best_individual, config_data['building_constraints'])

        # for individual in population:
        #     for chromosome in individual.chromosomes:
        #         print(chromosome)
        #     score = calculate_fitness(individual,config_data)
        #     print("Fitness: ",score)
        #     individual.fitness = score

if __name__ == "__main__":
    run_optimization(100,5,3,0.8,0.1)