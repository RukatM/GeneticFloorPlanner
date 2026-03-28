import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, Iterable, List, Tuple

from shapely.geometry import Polygon, box
from shapely.ops import unary_union


EPS = 1e-9


@dataclass(frozen=True)
class RoomRect:
    room: object
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float
    area: float
    cx: float
    cy: float
    poly: object


def build_room_rect(room) -> RoomRect:
    x1 = room.x
    y1 = room.y
    width = room.width
    height = room.height
    x2 = x1 + width
    y2 = y1 + height
    area = width * height
    return RoomRect(
        room=room,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        width=width,
        height=height,
        area=area,
        cx=x1 + width / 2.0,
        cy=y1 + height / 2.0,
        poly=box(x1, y1, x2, y2),
    )


def overlap_area(a: RoomRect, b: RoomRect) -> float:
    dx = min(a.x2, b.x2) - max(a.x1, b.x1)
    if dx <= EPS:
        return 0.0
    dy = min(a.y2, b.y2) - max(a.y1, b.y1)
    if dy <= EPS:
        return 0.0
    return dx * dy


def boundary_shared_length(a: RoomRect, b: RoomRect) -> float:
    if abs(a.x2 - b.x1) <= EPS or abs(b.x2 - a.x1) <= EPS:
        overlap = min(a.y2, b.y2) - max(a.y1, b.y1)
        return max(0.0, overlap)

    if abs(a.y2 - b.y1) <= EPS or abs(b.y2 - a.y1) <= EPS:
        overlap = min(a.x2, b.x2) - max(a.x1, b.x1)
        return max(0.0, overlap)

    return 0.0


def rect_distance(a: RoomRect, b: RoomRect) -> float:
    dx = max(a.x1 - b.x2, b.x1 - a.x2, 0.0)
    dy = max(a.y1 - b.y2, b.y1 - a.y2, 0.0)
    return math.hypot(dx, dy)


def center_distance(a: RoomRect, b: RoomRect) -> float:
    return math.hypot(a.cx - b.cx, a.cy - b.cy)


def build_type_index(chromosomes) -> Dict[str, List[object]]:
    by_type = defaultdict(list)
    for room in chromosomes:
        by_type[room.room_type].append(room)
    return by_type


def penalize_overlaps(rects_by_room: Dict[object, RoomRect], chromosomes: List[object]) -> float:
    penalty = 0.0
    for r1, r2 in combinations(chromosomes, 2):
        ov = overlap_area(rects_by_room[r1], rects_by_room[r2])
        if ov > 1e-3:
            penalty -= (ov ** 1.2) * 120.0
    return penalty


def penalize_area(chromosomes, min_area: Dict[str, float]) -> float:
    penalty = 0.0
    for room in chromosomes:
        required = min_area.get(room.room_type, 0.0)
        if required > 0.0:
            actual = room.width * room.height
            shortfall = max(0.0, (required - actual) / required)
            penalty -= shortfall * 400.0
    return penalty


def penalize_boundary(rects_by_room: Dict[object, RoomRect], building_poly: Polygon) -> float:
    penalty = 0.0
    for rect in rects_by_room.values():
        poly = rect.poly
        if not building_poly.covers(poly):
            outside_area = poly.difference(building_poly).area
            penalty -= 500.0 + outside_area * 50.0
    return penalty


def compute_adjacency_score(
    rooms_by_type: Dict[str, List[object]],
    rects_by_room: Dict[object, RoomRect],
    adjacency_requirements: List[Tuple[str, str]],
) -> float:
    score = 0.0

    for type1, type2 in adjacency_requirements:
        rooms1 = rooms_by_type.get(type1)
        rooms2 = rooms_by_type.get(type2)
        if not rooms1 or not rooms2:
            continue

        min_dist_sq = float("inf")

        if type1 == type2:
            for r1, r2 in combinations(rooms1, 2):
                a, b = rects_by_room[r1], rects_by_room[r2]
                dx = a.cx - b.cx
                dy = a.cy - b.cy
                d2 = dx * dx + dy * dy
                if d2 < min_dist_sq:
                    min_dist_sq = d2
        else:
            for r1 in rooms1:
                a = rects_by_room[r1]
                for r2 in rooms2:
                    b = rects_by_room[r2]
                    dx = a.cx - b.cx
                    dy = a.cy - b.cy
                    d2 = dx * dx + dy * dy
                    if d2 < min_dist_sq:
                        min_dist_sq = d2

        if min_dist_sq == float("inf"):
            continue

        if min_dist_sq <= 1.0:
            score += 30.0
        elif min_dist_sq <= 9.0:
            score += 10.0
        else:
            score -= (math.sqrt(min_dist_sq) - 3.0) * 5.0

    return score


def compute_separation_score(
    rooms_by_type: Dict[str, List[object]],
    rects_by_room: Dict[object, RoomRect],
    separation_requirements: List[Tuple[str, str]],
) -> float:
    score = 0.0

    for type1, type2 in separation_requirements:
        rooms1 = rooms_by_type.get(type1)
        rooms2 = rooms_by_type.get(type2)
        if not rooms1 or not rooms2:
            continue

        total_dist = 0.0
        count = 0

        if type1 == type2:
            for r1, r2 in combinations(rooms1, 2):
                total_dist += center_distance(rects_by_room[r1], rects_by_room[r2])
                count += 1
        else:
            for r1 in rooms1:
                a = rects_by_room[r1]
                for r2 in rooms2:
                    total_dist += center_distance(a, rects_by_room[r2])
                    count += 1

        if count == 0:
            continue

        avg_dist = total_dist / count
        if avg_dist <= 1.0:
            score -= 30.0
        elif avg_dist <= 3.0:
            score -= 10.0
        else:
            score += (avg_dist - 3.0) * 5.0

    return score


def compute_usage_score(chromosomes, building_poly: Polygon) -> float:
    total_area = sum(room.width * room.height for room in chromosomes)
    building_area = building_poly.area
    usage_ratio = total_area / building_area if building_area > EPS else 0.0
    unused_area = building_area - total_area

    score = usage_ratio * 100.0
    score -= (unused_area ** 1.3) if unused_area > 0 else abs(unused_area) * 50.0
    return score


def compute_wall_contact_score(rects_by_room: Dict[object, RoomRect], building_poly: Polygon) -> float:
    exterior = building_poly.exterior
    score = 0.0
    for rect in rects_by_room.values():
        contact_length = rect.poly.intersection(exterior).length
        score += contact_length * 5.0
        score += 30.0 if contact_length > EPS else -20.0
    return score


def penalize_aspect_ratio(chromosomes) -> float:
    penalty = 0.0
    for room in chromosomes:
        if room.width > EPS and room.height > EPS:
            ratio = max(room.width / room.height, room.height / room.width)
            if ratio > 1.5:
                penalty -= (math.log(ratio) ** 2) * 150.0
    return penalty


def compute_shared_wall_score(
    rects_by_room: Dict[object, RoomRect],
    chromosomes: List[object],
    corridor_width: float,
) -> float:
    score = 0.0

    for r1, r2 in combinations(chromosomes, 2):
        a = rects_by_room[r1]
        b = rects_by_room[r2]

        shared = boundary_shared_length(a, b)
        if shared > EPS:
            score += shared * 2.0
            continue

        dist = rect_distance(a, b)
        if dist <= corridor_width + EPS:
            score += min(2.0 * (a.width + a.height), 2.0 * (b.width + b.height))

    return score


def compute_corridor_geometry(rects_by_room: Dict[object, RoomRect], building_poly: Polygon):
    room_union = unary_union([rect.poly for rect in rects_by_room.values()])
    corridor_area = building_poly.difference(room_union)

    if corridor_area.is_empty:
        return corridor_area, []

    corridors = list(corridor_area.geoms) if corridor_area.geom_type == "MultiPolygon" else [corridor_area]
    return corridor_area, corridors


def calculate_corridor_connectivity_score(
    rects_by_room: Dict[object, RoomRect],
    corridors: List[Polygon],
) -> float:
    if not corridors:
        return -500.0

    used_corridor_ids = set()
    rooms_without_corridor = 0

    for rect in rects_by_room.values():
        matched = False
        for i, corridor in enumerate(corridors):
            if rect.poly.exterior.intersects(corridor):
                used_corridor_ids.add(i)
                matched = True
                break
        if not matched:
            rooms_without_corridor += 1

    num_components = len(used_corridor_ids) + rooms_without_corridor
    disconnected_penalty = -75.0 * max(0, num_components - 1)
    dead_corridor_penalty = -150.0 * max(0, len(corridors) - 1)
    orphan_room_penalty = -100.0 * rooms_without_corridor

    return disconnected_penalty + dead_corridor_penalty + orphan_room_penalty


def reward_straight_corridors(corridors: List[Polygon]) -> float:
    if not corridors:
        return 0.0

    score = 0.0
    for corridor in corridors:
        minx, miny, maxx, maxy = corridor.bounds
        bbox_area = (maxx - minx) * (maxy - miny)
        actual_area = corridor.area
        rect_ratio = actual_area / bbox_area if bbox_area > EPS else 0.0

        if actual_area < 5.0:
            score += 10.0
        if rect_ratio > 0.85:
            score += 50.0 * rect_ratio
        else:
            score -= (1.0 - rect_ratio) * 50.0

    return score


def calculate_fitness(individual, config_data, debug: bool = False) -> float:
    chromosomes = individual.chromosomes
    min_area = {r["type"]: r.get("min_area", 0.0) for r in config_data.get("rooms", [])}
    building_poly = Polygon(
        [(p["x"], p["y"]) for p in config_data.get("building_constraints", [])]
    )

    rects_by_room = {room: build_room_rect(room) for room in chromosomes}
    rooms_by_type = build_type_index(chromosomes)

    adjacency_requirements = config_data.get("adjacency_requirements", [])
    separation_requirements = config_data.get("separation_requirements", [])
    corridor_width = config_data.get("corridor_width", 1.0)

    _, corridors = compute_corridor_geometry(rects_by_room, building_poly)

    scores = {
        "1. overlap_penalty": penalize_overlaps(rects_by_room, chromosomes),
        "2. area_penalty": penalize_area(chromosomes, min_area),
        "3. boundary_penalty": penalize_boundary(rects_by_room, building_poly),
        "4. adjacency_score": compute_adjacency_score(
            rooms_by_type, rects_by_room, adjacency_requirements
        ),
        "5. separation_score": compute_separation_score(
            rooms_by_type, rects_by_room, separation_requirements
        ),
        "6. usage_score": compute_usage_score(chromosomes, building_poly),
        "7. wall_contact_score": compute_wall_contact_score(rects_by_room, building_poly),
        "8. aspect_penalty": penalize_aspect_ratio(chromosomes),
        "9. shared_wall_score": compute_shared_wall_score(
            rects_by_room, chromosomes, corridor_width
        ),
        "10. corridor_connectivity_score": calculate_corridor_connectivity_score(
            rects_by_room, corridors
        ),
        "11. straight_corridor_score": reward_straight_corridors(corridors),
    }

    if debug:
        print_scores(scores)

    return sum(scores.values())


def print_scores(scores: Dict[str, float]):
    print("\n=== Fitness Breakdown ===")
    for key, value in scores.items():
        print(f"{key:<35}: {value:>8.2f}")