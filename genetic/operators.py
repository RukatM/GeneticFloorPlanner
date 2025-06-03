import random
import math

from .chromosome import Chromosome
from .individual import Individual

def initialize_population(config_data, population_size):
    """
    Creates an initial population of individuals
    """

    population = []
    room_definitions = config_data.get('rooms',[])

    #temporary constraints

    max_x_coord = 50
    max_y_coord = 50

    if not room_definitions:
        print("No room definitions found in config data")
        return population
    
    for _ in range(population_size):
        current_individual_chromosomes = []
        for room in room_definitions:
            room_type = room.get('type')
            min_area = room.get('min_area', 1) 
            count = room.get('count', 1)

            for _ in range(count):

                initial_width =max(1,int(math.sqrt(min_area)) + 3)
                width = random.randint(1, initial_width ) #temporary
                height = max(1, math.ceil(min_area / width))

                x = random.randint(0, max(0, max_x_coord - width))
                y = random.randint(0, max(0, max_y_coord - height))

                new_chromosome = Chromosome(room_type, x, y, width, height)
                current_individual_chromosomes.append(new_chromosome)
        
        new_individual = Individual(chromosomes=current_individual_chromosomes)
        population.append(new_individual)


    return population
