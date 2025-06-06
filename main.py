import sys
from inout.parser import parse_input_file
from genetic.operators import initialize_population
from genetic.evaluator import calculate_fitness

def run_optimization():
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
    population = initialize_population(config_data,5)

    if population:
        print("Population succefully initialised")

        for individual in population:
            for chromosome in individual.chromosomes:
                print(chromosome)
            score = calculate_fitness(individual,config_data)
            print("Fitness: ",score)
            individual.fitness = score

    else:
        print("Population initialisation failed")

if __name__ == "__main__":
    run_optimization()