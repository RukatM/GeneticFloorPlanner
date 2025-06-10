import copy
import math
from matplotlib.path import Path
from shapely.geometry import Polygon, box
import random
from .chromosome import Chromosome
from .individual import Individual


def initialize_population(config_data, population_size, building_outline):
    """
    Creates an initial population of individuals constrained by the building outline
    """

    population = []
    room_definitions = config_data.get('rooms', [])
    outline_points = [(p['x'], p['y']) for p in building_outline]
    building_path = Path(outline_points)

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
                max_attempts = 100
                for attempt in range(max_attempts):
                    initial_width = max(1, int(math.sqrt(min_area)) + 3)
                    width = random.randint(1, initial_width)
                    height = max(1, math.ceil(min_area / width))

                    min_x = min(p['x'] for p in building_outline)
                    max_x = max(p['x'] for p in building_outline) - width
                    min_y = min(p['y'] for p in building_outline)
                    max_y = max(p['y'] for p in building_outline) - height

                    if max_x <= min_x or max_y <= min_y:
                        continue

                    x = random.randint(min_x, max_x)
                    y = random.randint(min_y, max_y)

                    rect_points = [
                        (x, y),
                        (x + width, y),
                        (x, y + height),
                        (x + width, y + height),
                    ]

                    if all(building_path.contains_point(p) for p in rect_points):
                        new_chromosome = Chromosome(room_type, x, y, width, height)
                        current_individual_chromosomes.append(new_chromosome)
                        break
                else:
                    print(f"Could not place room {room_type} within constraints after {max_attempts} attempts")

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


def crossover(parent1, parent2):
    """
    Performs single-point crossover on two parents to create two children
    """

    if len(parent1.chromosomes) < 2:
        return Individual(chromosomes=parent1.chromosomes),Individual(chromosomes=parent2.chromosomes)
    
    crossover_point = random.randint(1, len(parent1.chromosomes) - 1)
    
    p1_chromosomes = list(parent1.chromosomes)
    p2_chromosomes = list(parent2.chromosomes)

    child1_chromosomes = copy.deepcopy(p1_chromosomes[:crossover_point] + p2_chromosomes[crossover_point:])
    child2_chromosomes = copy.deepcopy(p2_chromosomes[:crossover_point] + p1_chromosomes[crossover_point:])

    child1 = Individual(chromosomes=child1_chromosomes)
    child2 = Individual(chromosomes=child2_chromosomes)

    return child1,child2


def mutate(individual, mutation_prob, building_outline):
    """
    Performs mutation on an individual, ensuring chromosomes stay within the building shape.
    """
    building_polygon = Polygon([(p['x'], p['y']) for p in building_outline])

    for chromosome in individual.chromosomes:
        if random.random() < mutation_prob:
            mutation_type = random.choice(['position', 'size'])

            original_x, original_y = chromosome.x, chromosome.y
            original_width, original_height = chromosome.width, chromosome.height

            if mutation_type == 'position':
                axis = random.choice(['x', 'y'])
                change = random.choice([-1, 1])

                if axis == 'x':
                    chromosome.x += change
                else:
                    chromosome.y += change

            elif mutation_type == 'size':
                dim_to_change = random.choice(['width', 'height'])
                change = random.choice([-2, 2])

                if dim_to_change == 'width':
                    chromosome.width = max(1, chromosome.width + change)
                else:
                    chromosome.height = max(1, chromosome.height + change)

            rect = box(chromosome.x, chromosome.y,
                       chromosome.x + chromosome.width,
                       chromosome.y + chromosome.height)

            if not building_polygon.contains(rect):
                chromosome.x, chromosome.y = original_x, original_y
                chromosome.width, chromosome.height = original_width, original_height

