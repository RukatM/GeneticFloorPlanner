import sys

from genetic.evolution import run_evolution
from inout.parser import parse_input_file
from genetic.operators import initialize_population
from visualization.gui import preview

NUM_GENERATIONS = 100
POPULATION_SIZE = 50
TOURNAMENT_SIZE = 3
CROSSOVER_PROB = 0.8
MUTATION_PROB = 0.1


def main():
    """
    Main function to run the genetic algorithm optimization.
    """
    
    input_filepath = "data/building_example.json"
    config_data = parse_input_file(input_filepath)
    building_constraints = config_data["building_constraints"]

    if not config_data:
        print("Error: Could not load configuration data. Exiting.")
        sys.exit(1) 

    print("Configuration loaded successfully")

    print("Initializing population")
    population = initialize_population(config_data, POPULATION_SIZE, building_constraints)

    if not population:
        print("Population initialisation failed")
        sys.exit(2)
    else:
        print("Population succefully initialised")

    final_population = run_evolution(population, config_data, NUM_GENERATIONS, POPULATION_SIZE, TOURNAMENT_SIZE, CROSSOVER_PROB, MUTATION_PROB)

    best_individual = max(final_population, key=lambda individual: individual.fitness)
    preview(best_individual, building_constraints)


if __name__ == "__main__":
    main()