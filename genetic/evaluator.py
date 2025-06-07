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


def get_intersection_area(room1, room2):
    box1 = box(room1.x, room1.y, room1.x + room1.width, room1.y + room1.height)
    box2 = box(room2.x, room2.y, room2.x + room2.width, room2.y + room2.height)
    intersection = box1.intersection(box2)
    return intersection.area if not intersection.is_empty else 0


def rooms_distance(room1, room2):
    """
    Oblicza euklidesową odległość między środkami dwóch pokoi.
    """
    cx1, cy1 = get_room_center(room1)
    cx2, cy2 = get_room_center(room2)
    return math.hypot(cx1 - cx2, cy1 - cy2)

def has_access_to_wall(room, building_poly, tolerance=1.0):
    # Sprawdza czy którykolwiek bok pokoju jest w odległości <= tolerance od ściany
    room_box = box(room.x, room.y, room.x + room.width, room.y + room.height)
    for side in building_poly.exterior.coords:
        if building_poly.exterior.distance(room_box) <= tolerance:
            return True
    return False


def are_rooms_adjacent(r1, r2, min_passage=0.8):
    # Zwraca True jeśli pokoje stykają się lub są bardzo blisko siebie
    room1 = box(r1.x, r1.y, r1.x + r1.width, r1.y + r1.height)
    room2 = box(r2.x, r2.y, r2.x + r2.width, r2.y + r2.height)
    return room1.distance(room2) <= min_passage


def check_room_accessibility(chromosomes, building_poly):
    """Sprawdza, czy każdy pokój ma połączenie z zewnętrzną ścianą bezpośrednio lub przez inne pokoje."""
    from collections import deque

    # Zbuduj graf sąsiedztwa
    adjacency = {i: [] for i in range(len(chromosomes))}
    for i, r1 in enumerate(chromosomes):
        for j, r2 in enumerate(chromosomes):
            if i != j and are_rooms_adjacent(r1, r2):
                adjacency[i].append(j)

    # Znajdź pokoje z dostępem do ściany
    accessible = set()
    for i, room in enumerate(chromosomes):
        if has_access_to_wall(room, building_poly):
            accessible.add(i)

    # BFS by znaleźć wszystkie pokoje dostępne przez inne
    queue = deque(accessible)
    visited = set(accessible)

    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return visited == set(range(len(chromosomes)))  # True jeśli wszystkie pokoje są dostępne


def calculate_fitness(individual, config_data):
    score = 0.0
    chromosomes = individual.chromosomes
    min_area = {room.get('type'): room.get('min_area', 0) for room in config_data.get('rooms', [])}
    building_poly = Polygon([(p['x'], p['y']) for p in config_data.get('building_constraints', [])])

    # 1. Kolizje między pokojami
    for r1, r2 in combinations(chromosomes, 2):
        if check_collision(r1, r2):
            score -= 1000

    # 2. Spełnienie minimalnych powierzchni
    for room in chromosomes:
        if room.get_area() >= min_area.get(room.room_type, 0):
            score += 200
        else:
            score -= 100

    # 3. Czy pokój mieści się w granicach budynku
    for room in chromosomes:
        room_box = box(room.x, room.y, room.x + room.width, room.y + room.height)
        if not building_poly.contains(room_box):
            score -= 1000

    # 4. Wymagania sąsiedztwa
    for type1, type2 in config_data.get('adjacency_requirements', []):
        rooms1 = [r for r in chromosomes if r.room_type == type1]
        rooms2 = [r for r in chromosomes if r.room_type == type2]
        if rooms1 and rooms2:
            min_dist = min(rooms_distance(r1, r2) for r1 in rooms1 for r2 in rooms2)
            score += 20 if min_dist <= 3 else -min_dist * 5

    # 5. Wykorzystanie powierzchni budynku
    total_area = sum(room.get_area() for room in chromosomes)
    usage_ratio = total_area / building_poly.area if building_poly.area > 0 else 0
    score += usage_ratio * 100  # większa waga

    # 6. Przynajmniej jeden bok pokoju dotyka zewnętrznej ściany
    for room in chromosomes:
        touches_wall = False
        if math.isclose(room.x, building_poly.bounds[0], abs_tol=1e-3):
            touches_wall = True
        if math.isclose(room.y, building_poly.bounds[1], abs_tol=1e-3):
            touches_wall = True
        if math.isclose(room.x + room.width, building_poly.bounds[2], abs_tol=1e-3):
            touches_wall = True
        if math.isclose(room.y + room.height, building_poly.bounds[3], abs_tol=1e-3):
            touches_wall = True
        if touches_wall:
            score += 30
        else:
            score -= 20  # kara za brak dostępu do światła dziennego

    # 7. Faworyzuj bardziej kwadratowe pomieszczenia
    for room in chromosomes:
        aspect_ratio = max(room.width / room.height, room.height / room.width)
        squareness_penalty = (aspect_ratio - 1) * 10 if aspect_ratio > 1.5 else 0
        score -= squareness_penalty

    # 8. Unikaj pustych kieszeni – prosty wskaźnik: pole niewykorzystane
    unused_area = building_poly.area - total_area
    score -= unused_area * 0.5  # kara za niewykorzystanie przestrzeni

    # 9. Minimalizacja odległości do wejścia (jeśli zdefiniowano)
    entrance = config_data.get("entrance")  # np. {'x': 0, 'y': 0}
    if entrance:
        for room in chromosomes:
            room_center = (room.x + room.width / 2, room.y + room.height / 2)
            dist = math.dist((entrance['x'], entrance['y']), room_center)
            score -= dist * 0.2  # lekkie premiowanie bliskości

    # 10. Sprawdzenie dostępności przejść
    if not check_room_accessibility(chromosomes, building_poly):
        score -= 1000  # Silna kara za brak dostępu
    else:
        score += 100  # Premia za prawidłowy dostęp


    return score
