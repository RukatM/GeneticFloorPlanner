from mpi4py import MPI
import sys
import time
from genetic.evolution import run_evolution
from genetic.evolution_parallel import run_evolution_parallel
from inout.parser import parse_input_file
from genetic.operators import initialize_population
from visualization.gui import preview

NUM_GENERATIONS = 500
POPULATION_SIZE = 50
TOURNAMENT_SIZE = 6
CROSSOVER_PROB = 0.8
MUTATION_PROB = 0.5


def main():
    """
    Main function to run the genetic algorithm optimization.
    """
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    input_filepath = "data/building_example.json"
    config_data = parse_input_file(input_filepath)
    building_constraints = config_data["building_constraints"]

    if not config_data:
        if rank == 0:
            print("Error: Could not load configuration data. Exiting.")
        sys.exit(1)

    if rank == 0:
        print("Configuration loaded successfully")
        print("Initializing population")

    population = initialize_population(config_data, POPULATION_SIZE, building_constraints)

    if not population:
        if rank == 0:
            print("Population initialisation failed")
        sys.exit(2)
    else:
        if rank == 0:
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
        MUTATION_PROB
    )

    if rank == 0:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nEvolution completed in {elapsed_time:.2f} seconds")

        best_individual = max(final_population, key=lambda individual: individual.fitness)
        preview(best_individual, building_constraints)


if __name__ == "__main__":
    main()
