import json

def export_individual(individual, generation_index, file_path):
    """
    Export results to a JSON configuration file.
    """
    
    result_data = {
        "generation": generation_index,
        "fitness": individual.fitness,
        "rooms": []
    }

    for room in individual.chromosomes:
        room_data = {
            "type": room.room_type,
            "x": room.x,
            "y": room.y,
            "width": room.width,
            "height": room.height
        }
        result_data["rooms"].append(room_data)

    try:
        with open(file_path, 'w') as f:
            json.dump(result_data, f, indent=4)
        return True
    except Exception as e:
        return False