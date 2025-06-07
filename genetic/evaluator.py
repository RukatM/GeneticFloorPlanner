

def check_collision(room1,room2):
    """
    Checks if two rooms overlap.
    """
    
    x_collision = (room1.x < room2.x + room2.width) and room2.x < room1.x + room1.width
    y_collision = (room1.y < room2.y + room2.height) and room2.y < room1.y + room1.height

    return x_collision and y_collision

def calculate_fitness(individual, config_data):
    """
    Calculate fitness score for an individual.
    """
    score = 0.0
    collision_counter = 0
    chromosomes = individual.chromosomes
    min_area = {}

    for room in config_data.get('rooms', []):
        min_area[room.get('type')] = room.get('min_area')

    if len(chromosomes) > 1:
        for i in range(len(chromosomes)):
            for j in range(i+1,len(chromosomes)):
                if check_collision(chromosomes[i],chromosomes[j]):
                    collision_counter += 1

    score -= collision_counter * 100

    min_area_rooms = 0 
    for chromosome in chromosomes:
        if chromosome.get_area() >= min_area[chromosome.room_type]:
            min_area_rooms += 1

    score += min_area_rooms * 10.0

    #do uzupełnienia
    return score