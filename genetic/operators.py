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

def tournament_selection(population, tournament_size):
    """
    Select a parent from population using tournament selection
    """

    if len(population) < tournament_size:
        return max(population,key = lambda individual : individual.fitness)
    

    tournament = random.sample(population,tournament_size)
    return max(tournament,key = lambda individual : individual.fitness)

def crossover(parent1,parent2):
    """
    Performs single-point crossover on two parents to create two children
    """

    if len(parent1.chromosomes) < 2:
        return (Individual(chromosomes=parent1.chromosomes),Individual(chromosomes=parent2.chromosomes))
    
    crossover_point = random.randint(1, len(parent1.chromosomes) - 1)
    
    p1_chromosomes = list(parent1.chromosomes)
    p2_chromosomes = list(parent2.chromosomes)

    child1_chromosomes = p1_chromosomes[:crossover_point] + p2_chromosomes[crossover_point:]
    child2_chromosomes = p2_chromosomes[:crossover_point] + p1_chromosomes[crossover_point:]

    child1 = Individual(chromosomes=child1_chromosomes)
    child2 = Individual(chromosomes=child2_chromosomes)

    return (child1,child2)

def mutate(individual, mutation_prob, config_data):
    """
    Performs mutation on an individual
    """

    #temporary x y constraints
    max_x= 50
    max_y= 50

    for chromosome in individual.chromosomes:
        if random.random() < mutation_prob:
            mutation_type = random.choice(['position','size'])

            if mutation_type == 'position':
                axis = random.choice(['x', 'y'])
                change = random.choice([-1, 1])
                
                if axis == 'x':
                    chromosome.x += change
                    chromosome.x = max(0, min(chromosome.x, max_x - chromosome.width))
                else: 
                    chromosome.y += change
                    chromosome.y = max(0, min(chromosome.y, max_y - chromosome.height))
            
            elif mutation_type == 'size':
                dim_to_change = random.choice(['width', 'height'])
                
                if dim_to_change == 'width':
                    chromosome.width += 1
                else: 
                    chromosome.height += 1
                
                chromosome.width = max(1, chromosome.width)
                chromosome.height = max(1, chromosome.height)



