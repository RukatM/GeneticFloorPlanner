# main.py

from mpi4py import MPI
import sys
import time

from genetic.evolution_parallel import run_evolution_parallel
# ZMIANA: Poprawiona nazwa importu
from inout.parser import parse_input_file
from genetic.operators import initialize_population
# ZMIANA: Poprawiona nazwa importu i dodanie QApplication
from visualization.renderer import preview
from visualization.main_window import MainWindow
from PyQt5.QtWidgets import QApplication


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    params = None
    config_data = None
    
    if rank == 0:
        print("Proces 0: Uruchamianie interfejsu użytkownika...")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        app.exec_() 

        params = window.get_params()
        if params is None:
            print("Anulowano. Zamykanie aplikacji.")
            params = {'terminate': True} # Sygnał do zakończenia dla innych procesów
    
    # NOWOŚĆ: Proces 0 rozsyła zebrane parametry do wszystkich
    params = comm.bcast(params, root=0)

    if params.get('terminate'):
        return

    if rank == 0:
        input_filepath = params['config_file']
        config_data = parse_input_file(input_filepath)
        if not config_data:
            print("Error: Could not load configuration data. Exiting.")
            comm.Abort() # Zatrzymujemy wszystkie procesy MPI w razie błędu pliku

    config_data = comm.bcast(config_data, root=0)

    # ZMIANA: Parametry są pobierane ze słownika 'params' z GUI
    num_generations = params["num_generations"]
    population_size = params["population_size"]
    tournament_size = params["tournament_size"]
    crossover_prob = params["crossover_prob"]
    mutation_prob = params["mutation_prob"]
    
    building_constraints = config_data["building_constraints"]
    entrances = config_data["entrances"]

    population = None
    if rank == 0:
        print("Configuration loaded successfully")
        print("Initializing population")
        # ZMIANA: Przekazujemy poprawne parametry do inicjalizacji
        population = initialize_population(config_data, population_size,building_constraints)

        if not population:
            print("Population initialisation failed")
            comm.Abort()
        else:
            print("Population successfully initialised")

    start_time = 0
    if rank == 0:
        start_time = time.time()

    # ZMIANA: Przekazujemy poprawione parametry do funkcji ewolucji
    final_population = run_evolution_parallel(
        population,
        config_data,
        num_generations,
        population_size,
        tournament_size,
        crossover_prob,
        mutation_prob
    )

    if final_population is None:
        return

    if rank == 0:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nEvolution completed in {elapsed_time:.2f} seconds")

        best_individual = max(final_population, key=lambda individual: individual.fitness)
        # Usunięto calculate_fitness, bo jest częścią pętli ewolucyjnej
        
        # ZMIANA: Uruchomienie `preview` wymaga działającej pętli QApplication
        print("Wyświetlanie najlepszego wyniku...")
        app = QApplication(sys.argv)
        preview(best_individual, building_constraints, entrances)
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()