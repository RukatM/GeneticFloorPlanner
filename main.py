import sys
from inout.parser import parse_input_file
from genetic.operators import initialize_population
from genetic.evaluator import calculate_fitness

def run_optimization(num_generations,population_size):
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
    population = initialize_population(config_data,population_size)

    if not population:
        print("Population initialisation failed")
        sys.exit(2) 

    
    else:
        print("Population succefully initialised")

        for generation in range(num_generations):
            for individual in population:
                individual.fitness = calculate_fitness(individual,config_data)

            best_individual = max(population,key = lambda individual : individual.fitness)
            print(f"Generacja:{generation + 1} najlepszy osobnik: {best_individual}")


        # for individual in population:
        #     for chromosome in individual.chromosomes:
        #         print(chromosome)
        #     score = calculate_fitness(individual,config_data)
        #     print("Fitness: ",score)
        #     individual.fitness = score

if __name__ == "__main__":
    run_optimization(100,5)