import time

from genetic.evolution_parallel import run_evolution_parallel
from genetic.operators import initialize_population
from inout.parser import parse_input_file


def run_evolution(comm, params):
    rank = comm.Get_rank()
    config_data = None
    params = comm.bcast(params, root=0)

    if rank == 0:
        input_filepath = params['config_file']
        config_data = parse_input_file(input_filepath)
        if not config_data:
            print("Error: Could not load configuration data. Exiting.")
            comm.Abort()

    config_data = comm.bcast(config_data, root=0)
    building_constraints = config_data["building_constraints"]

    population = None
    if rank == 0:
        print("Configuration loaded successfully")
        print("Initializing population")
        population = initialize_population(config_data, params["population_size"], building_constraints)

        if not population:
            print("Population initialisation failed")
            comm.Abort()
        else:
            print("Population successfully initialised")

    start_time = 0
    if rank == 0:
        start_time = time.time()

    final_population, hall_of_fame = run_evolution_parallel(
        population,
        config_data,
        params["num_generations"],
        params["population_size"],
        params["tournament_size"],
        params["crossover_prob"],
        params["mutation_prob"]
    )

    if final_population is None:
        return None

    if rank == 0:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nEvolution completed in {elapsed_time:.2f} seconds")

        best_individual = max(final_population, key=lambda individual: individual.fitness)
        print(best_individual)

    return hall_of_fame
