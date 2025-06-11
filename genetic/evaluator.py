import math
from itertools import combinations
from typing import Dict, List, Tuple
import networkx as nx
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def get_room_box(room) -> Polygon:
    return box(room.x, room.y, room.x + room.width, room.y + room.height)


def get_room_center(room) -> Tuple[float, float]:
    return room.x + room.width / 2, room.y + room.height / 2


def penalize_overlaps(room_pairs, room_boxes) -> float:
    penalty = 0.0
    for r1, r2 in room_pairs:
        overlap = room_boxes[r1].intersection(room_boxes[r2]).area
        if overlap > 1e-3:
            penalty -= (overlap ** 1.2) * 120
    return penalty


def penalize_area(chromosomes, min_area: Dict[str, float]) -> float:
    penalty = 0.0
    for room in chromosomes:
        required = min_area.get(room.room_type, 0)
        if required > 0:
            actual = room.get_area()
            shortfall = max(0, (required - actual) / required)
            penalty -= shortfall * 400
    return penalty


def penalize_boundary(room_boxes: Dict, building_poly: Polygon) -> float:
    penalty = 0.0
    for room_box in room_boxes.values():
        if not building_poly.covers(room_box):
            outside_area = room_box.difference(building_poly).area
            penalty -= 500 + outside_area * 50
    return penalty


def compute_adjacency_score(chromosomes, room_centers, adjacency_requirements: List[Tuple[str, str]]) -> float:
    score = 0.0
    for type1, type2 in adjacency_requirements:
        rooms1 = [r for r in chromosomes if r.room_type == type1]
        rooms2 = [r for r in chromosomes if r.room_type == type2]

        if rooms1 and rooms2:
            min_dist = min(
                math.hypot(room_centers[r1][0] - room_centers[r2][0], room_centers[r1][1] - room_centers[r2][1])
                for r1 in rooms1 for r2 in rooms2
            )
            if min_dist <= 1:
                score += 30
            elif min_dist <= 3:
                score += 10
            else:
                score -= (min_dist - 3) * 5
    return score


def compute_separation_score(chromosomes, room_centers, separation_requirements: List[Tuple[str, str]]) -> float:
    score = 0.0
    for type1, type2 in separation_requirements:
        rooms1 = [r for r in chromosomes if r.room_type == type1]
        rooms2 = [r for r in chromosomes if r.room_type == type2]

        distances = []
        for r1 in rooms1:
            for r2 in rooms2:
                dist = math.hypot(
                    room_centers[r1][0] - room_centers[r2][0],
                    room_centers[r1][1] - room_centers[r2][1]
                )
                distances.append(dist)

        if distances:
            avg_dist = sum(distances) / len(distances)
            if avg_dist <= 1:
                score -= 30
            elif avg_dist <= 3:
                score -= 10
            else:
                score += (avg_dist - 3) * 5
    return score


def compute_usage_score(chromosomes, building_poly: Polygon) -> float:
    total_area = sum(room.get_area() for room in chromosomes)
    building_area = building_poly.area
    usage_ratio = total_area / building_area if building_area > 0 else 0
    unused_area = building_area - total_area

    score = usage_ratio * 100
    score -= (unused_area ** 1.3) if unused_area > 0 else abs(unused_area) * 50
    return score


def compute_wall_contact_score(room_boxes: Dict, building_poly: Polygon) -> float:
    score = 0.0
    for room_box in room_boxes.values():
        contact_length = room_box.intersection(building_poly.exterior).length
        score += contact_length * 5
        score += 30 if contact_length > 0 else -20
    return score


def penalize_aspect_ratio(chromosomes) -> float:
    penalty = 0.0
    for room in chromosomes:
        if room.width > 0 and room.height > 0:
            ratio = max(room.width / room.height, room.height / room.width)
            if ratio > 1.5:
                penalty -= (math.log(ratio) ** 2) * 150
    return penalty


def compute_shared_wall_score(room_pairs, room_boxes, corridor_width: float) -> float:
    score = 0.0
    for r1, r2 in room_pairs:
        box1, box2 = room_boxes[r1], room_boxes[r2]
        dist = box1.distance(box2)
        if dist < 1e-3:
            shared = box1.boundary.intersection(box2.boundary).length
            if shared > 0:
                score += shared * 2
        elif dist <= corridor_width:
            union_area = box1.union(box2).area
            overlap_area = union_area - (box1.area + box2.area)
            if overlap_area < 1e-2:
                score += min(box1.length, box2.length) * 2
    return score


def calculate_corridor_connectivity_score(room_boxes: Dict, building_poly: Polygon) -> float:
    corridor_area = building_poly.difference(unary_union(list(room_boxes.values())))

    if corridor_area.is_empty:
        return -500

    corridor_polygons = list(corridor_area.geoms) if corridor_area.geom_type == 'MultiPolygon' else [corridor_area]
    num_corridors = len(corridor_polygons)

    room_corridor_map = {}
    rooms_without_corridor = 0

    for room, room_box in room_boxes.items():
        connected = False
        for i, corridor in enumerate(corridor_polygons):
            if room_box.exterior.intersects(corridor):
                room_corridor_map[room] = i
                connected = True
                break
        if not connected:
            rooms_without_corridor += 1

    G = nx.Graph()
    G.add_nodes_from(room_boxes.keys())

    for r1, r2 in combinations(room_boxes.keys(), 2):
        if room_corridor_map.get(r1) == room_corridor_map.get(r2):
            G.add_edge(r1, r2)

    if len(G.nodes) > 0:
        num_components = nx.number_connected_components(G)
    else:
        num_components = len(room_boxes)

    disconnected_penalty = -75 * (num_components - 1)
    dead_corridor_penalty = -150 * (num_corridors - 1)
    orphan_room_penalty = -100 * rooms_without_corridor

    final_score = disconnected_penalty + dead_corridor_penalty + orphan_room_penalty
    return final_score


def reward_straight_corridors(room_boxes: Dict, building_poly: Polygon) -> float:
    corridor_area = building_poly.difference(unary_union(list(room_boxes.values())))
    if corridor_area.is_empty:
        return 0

    corridors = list(corridor_area.geoms) if corridor_area.geom_type == 'MultiPolygon' else [corridor_area]
    score = 0.0

    for corridor in corridors:
        minx, miny, maxx, maxy = corridor.bounds
        bbox_area = (maxx - minx) * (maxy - miny)
        actual_area = corridor.area

        rect_ratio = actual_area / bbox_area if bbox_area > 0 else 0

        if actual_area < 5:
            score += 10
        if rect_ratio > 0.85:
            score += 50 * rect_ratio
        else:
            score -= (1 - rect_ratio) * 50

    return score


def calculate_fitness(individual, config_data, debug=False) -> float:
    chromosomes = individual.chromosomes
    min_area = {r['type']: r.get('min_area', 0) for r in config_data.get('rooms', [])}
    building_poly = Polygon([(p['x'], p['y']) for p in config_data.get('building_constraints', [])])

    room_boxes = {room: get_room_box(room) for room in chromosomes}
    room_centers = {room: get_room_center(room) for room in chromosomes}
    room_pairs = list(combinations(chromosomes, 2))

    adjacency_requirements = config_data.get('adjacency_requirements', [])
    separation_requirements = config_data.get('separation_requirements', [])
    corridor_width = config_data.get("corridor_width", 1.0)

    scores = {
        '1. overlap_penalty': penalize_overlaps(room_pairs, room_boxes),
        '2. area_penalty': penalize_area(chromosomes, min_area),
        '3. boundary_penalty': penalize_boundary(room_boxes, building_poly),
        '4. adjacency_score': compute_adjacency_score(chromosomes, room_centers, adjacency_requirements),
        '5. separation_score': compute_separation_score(chromosomes, room_centers, separation_requirements),
        '6. usage_score': compute_usage_score(chromosomes, building_poly),
        '7. wall_contact_score': compute_wall_contact_score(room_boxes, building_poly),
        '8. aspect_penalty': penalize_aspect_ratio(chromosomes),
        '9. shared_wall_score': compute_shared_wall_score(room_pairs, room_boxes, corridor_width),
        '10. corridor_connectivity_score': calculate_corridor_connectivity_score(room_boxes, building_poly),
        '11. straight_corridor_score': reward_straight_corridors(room_boxes, building_poly),
    }

    if debug:
        print_scores(scores)

    return sum(scores.values())


def print_scores(scores: Dict[str, float]):
    print("\n=== Fitness Breakdown ===")
    for key, value in scores.items():
        print(f"{key:<35}: {value:>8.2f}")
