import math
from itertools import combinations
from shapely.geometry import Polygon, box


def check_collision(room1, room2):
    """
    Sprawdza, czy dwa pokoje się nachodzą.
    """
    box1 = box(room1.x, room1.y, room1.x + room1.width, room1.y + room1.height)
    box2 = box(room2.x, room2.y, room2.x + room2.width, room2.y + room2.height)
    return box1.intersects(box2)


def get_room_center(room):
    """
    Zwraca środek pokoju jako krotkę (x, y).
    """
    return (room.x + room.width / 2, room.y + room.height / 2)


def rooms_distance(room1, room2):
    """
    Oblicza euklidesową odległość między środkami dwóch pokoi.
    """
    cx1, cy1 = get_room_center(room1)
    cx2, cy2 = get_room_center(room2)
    return math.hypot(cx1 - cx2, cy1 - cy2)


def calculate_fitness(individual, config_data):
    """
    Oblicza dopasowanie (fitness) rozkładu pomieszczeń na podstawie:
    - kolizji
    - minimalnych powierzchni
    - ograniczeń budynku
    - wymagań sąsiedztwa
    - stopnia wykorzystania powierzchni
    """
    score = 0.0
    chromosomes = individual.chromosomes
    min_area = {room.get('type'): room.get('min_area', 0) for room in config_data.get('rooms', [])}
    building_poly = Polygon([(p['x'], p['y']) for p in config_data.get('building_constraints', [])])

    # 1. Kolizje między pokojami
    for r1, r2 in combinations(chromosomes, 2):
        if check_collision(r1, r2):
            score -= 200

    # 2. Spełnienie minimalnych powierzchni
    for room in chromosomes:
        if room.get_area() >= min_area.get(room.room_type, 0):
            score += 50

    # 3. Czy pokój mieści się w granicach budynku
    for room in chromosomes:
        room_box = box(room.x, room.y, room.x + room.width, room.y + room.height)
        if not building_poly.contains(room_box):
            score -= 500

    # 4. Wymagania sąsiedztwa
    for type1, type2 in config_data.get('adjacency_requirements', []):
        rooms1 = [r for r in chromosomes if r.room_type == type1]
        rooms2 = [r for r in chromosomes if r.room_type == type2]
        if rooms1 and rooms2:
            min_dist = min(rooms_distance(r1, r2) for r1 in rooms1 for r2 in rooms2)
            score += 10 if min_dist < 5 else -min_dist

    # 5. Wykorzystanie powierzchni budynku
    total_area = sum(room.get_area() for room in chromosomes)
    usage_ratio = total_area / building_poly.area if building_poly.area > 0 else 0
    score += usage_ratio * 50

    return score
