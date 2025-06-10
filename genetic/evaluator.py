import math
from itertools import combinations

import networkx as nx
from shapely.geometry import Polygon, box, Point
from shapely.geometry.linestring import LineString
from shapely.ops import unary_union


def check_collision(room1, room2, tolerance=1e-3):
    """
    Sprawdza, czy dwa pokoje się nachodzą (z uwzględnieniem tolerancji).
    """
    box1 = box(room1.x, room1.y, room1.x + room1.width, room1.y + room1.height)
    box2 = box(room2.x, room2.y, room2.x + room2.width, room2.y + room2.height)
    intersection = box1.intersection(box2)
    return not intersection.is_empty and intersection.area > tolerance


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
    room_box = box(room.x, room.y, room.x + room.width, room.y + room.height)
    return building_poly.exterior.distance(room_box) <= tolerance


def are_rooms_adjacent(r1, r2, min_passage=0.8):
    """
    Zwraca True jeśli pokoje stykają się lub są bardzo blisko siebie.
    """
    room1 = box(r1.x, r1.y, r1.x + r1.width, r1.y + r1.height)
    room2 = box(r2.x, r2.y, r2.x + r2.width, r2.y + r2.height)
    return room1.distance(room2) <= min_passage


def wall_contact_length(room, building_poly):
    room_box = box(room.x, room.y, room.x + room.width, room.y + room.height)
    intersection = room_box.intersection(building_poly.exterior)
    return intersection.length if not intersection.is_empty else 0


def calculate_corridor_connectivity_score(room_boxes, building_poly):
    # 1. Wyznacz pustą przestrzeń
    corridor_area = building_poly
    for box in room_boxes.values():
        corridor_area = corridor_area.difference(box)

    # 2. Znajdź komponenty spójne korytarza
    if corridor_area.is_empty:
        return -500  # żadna dostępność

    if corridor_area.geom_type == 'Polygon':
        corridor_polygons = [corridor_area]
    elif corridor_area.geom_type == 'MultiPolygon':
        corridor_polygons = list(corridor_area.geoms)
    else:
        return -500  # coś poszło nie tak

    # 3. Dla każdego pokoju: sprawdź z którym kawałkiem korytarza się łączy
    room_corridor_map = {}
    for room, room_box in room_boxes.items():
        for i, corridor in enumerate(corridor_polygons):
            if room_box.exterior.intersects(corridor):
                room_corridor_map[room] = i
                break

    # 4. Budujemy graf
    G = nx.Graph()
    rooms = list(room_boxes.keys())
    G.add_nodes_from(rooms)

    # 5. Łączymy pokoje, które należą do tej samej części korytarza
    for i, r1 in enumerate(rooms):
        for r2 in rooms[i+1:]:
            if room_corridor_map.get(r1) is not None and room_corridor_map.get(r1) == room_corridor_map.get(r2):
                G.add_edge(r1, r2)

    # 6. Sprawdzamy spójność
    if nx.is_connected(G):
        return 100  # pełna dostępność
    else:
        # kara za liczbę niespójnych komponentów
        components = list(nx.connected_components(G))
        return -100 * (len(components) - 1)


def calculate_fitness(individual, config_data, debug=False):
    chromosomes = individual.chromosomes

    # Konfiguracja
    min_area = {room.get('type'): room.get('min_area', 0) for room in config_data.get('rooms', [])}
    building_poly = Polygon([(p['x'], p['y']) for p in config_data.get('building_constraints', [])])
    room_boxes = {room: box(room.x, room.y, room.x + room.width, room.y + room.height) for room in chromosomes}

    scores = {}

    # 1. Kara za nakładające się pokoje
    overlap_penalty = 0.0
    for r1, r2 in combinations(chromosomes, 2):
        overlap = room_boxes[r1].intersection(room_boxes[r2]).area
        if overlap > 1e-3:
            overlap_penalty -= math.pow(overlap, 1.2) * 120
    scores['1. overlap_penalty'] = overlap_penalty

    # 2. Kara za zbyt małe pokoje
    area_penalty = 0.0
    for room in chromosomes:
        actual_area = room.get_area()
        required_area = min_area.get(room.room_type, 0)
        if required_area > 0 and actual_area < required_area:
            shortfall_ratio = (required_area - actual_area) / required_area
            area_penalty -= shortfall_ratio * 300
    scores['2. area_penalty'] = area_penalty

    # 3. Kara za wyjście poza budynek
    boundary_penalty = 0.0
    for room in chromosomes:
        room_box = room_boxes[room]
        if not building_poly.covers(room_box):
            outside_area = room_box.difference(building_poly).area
            boundary_penalty -= 500 + outside_area * 50
    scores['3. boundary_penalty'] = boundary_penalty

    # 4. Wymagania przylegania
    adjacency_score = 0.0
    for type1, type2 in config_data.get('adjacency_requirements', []):
        rooms1 = [r for r in chromosomes if r.room_type == type1]
        rooms2 = [r for r in chromosomes if r.room_type == type2]
        if rooms1 and rooms2:
            min_dist = min(rooms_distance(r1, r2) for r1 in rooms1 for r2 in rooms2)
            if min_dist <= 1:
                adjacency_score += 30
            elif min_dist <= 3:
                adjacency_score += 10
            else:
                adjacency_score -= (min_dist - 3) * 5
    scores['4. adjacency_score'] = adjacency_score

    # 5. Kara za rozproszenie grup
    dispersion_penalty = 0.0
    grouped_types = ['sypialnia', 'łazienka']
    grouped_rooms = [r for r in chromosomes if r.room_type in grouped_types]
    if len(grouped_rooms) >= 2:
        avg_dist = sum(rooms_distance(r1, r2) for r1, r2 in combinations(grouped_rooms, 2)) / len(grouped_rooms)
        if avg_dist > 10:
            dispersion_penalty -= (avg_dist - 10) * 10
    scores['5. dispersion_penalty'] = dispersion_penalty

    # 6. Użycie przestrzeni budynku
    total_area = sum(room.get_area() for room in chromosomes)
    usage_ratio = total_area / building_poly.area if building_poly.area > 0 else 0
    usage_score = usage_ratio * 100
    unused_area = building_poly.area - total_area
    if unused_area > 0:
        usage_score -= math.pow(unused_area, 1.3)
    else:
        usage_score -= abs(unused_area) * 50
    scores['6. usage_score'] = usage_score

    # 7. Kontakt pokoi ze ścianą
    wall_contact_score = 0.0
    for room in chromosomes:
        room_box = room_boxes[room]
        contact_length = room_box.intersection(building_poly.exterior).length
        wall_contact_score += contact_length * 5
        if has_access_to_wall(room, building_poly):
            wall_contact_score += 30
        else:
            wall_contact_score -= 20
    scores['7. wall_contact_score'] = wall_contact_score

    # 8. Proporcje pokoi
    aspect_penalty = 0.0
    for room in chromosomes:
        if room.width > 0 and room.height > 0:
            aspect_ratio = max(room.width / room.height, room.height / room.width)
            if aspect_ratio > 1.5:  # niższy próg
                aspect_penalty -= (math.log(aspect_ratio) ** 2) * 150  # silniejsza kara
    scores['8. aspect_penalty'] = aspect_penalty

    # 9. Wspólne ściany
    shared_wall_score = 0.0
    for r1, r2 in combinations(chromosomes, 2):
        box1 = room_boxes[r1]
        box2 = room_boxes[r2]
        dist = box1.distance(box2)

        if dist < 1e-3:
            shared_length = box1.boundary.intersection(box2.boundary).length
            if shared_length > 0:
                shared_wall_score += shared_length * 2
        elif dist <= config_data["corridor_width"]:
            overlap_area = box1.union(box2).area - (box1.area + box2.area)
            if overlap_area < 1e-2:
                proximity_length = min(box1.length, box2.length)
                shared_wall_score += proximity_length * 2
    scores['10. shared_wall_score'] = shared_wall_score

    corridor_score = calculate_corridor_connectivity_score(room_boxes, building_poly)
    scores['11. corridor_connectivity_score'] = corridor_score

    total_score = sum(scores.values())

    if debug:
        for key, value in scores.items():
            print(f"  {key}: {value}")

    return total_score
