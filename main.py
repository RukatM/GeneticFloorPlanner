from mpi4py import MPI
import sys
import time

from genetic.evaluator import calculate_fitness
from genetic.evolution_parallel import run_evolution_parallel
from inout.parser import parse_input_file
from genetic.operators import initialize_population
from visualization.renderer import preview

NUM_GENERATIONS = 300
POPULATION_SIZE = 250
TOURNAMENT_SIZE = 6
CROSSOVER_PROB = 0.8
MUTATION_PROB = 0.6


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    input_filepath = "data/building_example.json"
    config_data = parse_input_file(input_filepath)
    building_constraints = config_data["building_constraints"]

    population = None
    if rank == 0:
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
            print("Population successfully initialised")

    start_time = 0
    if rank == 0:
        start_time = time.time()

    final_population = run_evolution_parallel(
        population,
        config_data,
        NUM_GENERATIONS,
        POPULATION_SIZE,
        TOURNAMENT_SIZE,
        CROSSOVER_PROB,
        MUTATION_PROB,
        comm,
        debug=True
    )

    if final_population is None:
        return

    if rank == 0:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nEvolution completed in {elapsed_time:.2f} seconds")

        best_individual = max(final_population, key=lambda individual: individual.fitness)
        calculate_fitness(best_individual, config_data, debug=True)
        preview(best_individual, building_constraints)


if __name__ == "__main__":
    main()
