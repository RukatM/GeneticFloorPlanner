import json

def parse_input_file(filepath):
    """
    Loads and parses a JSON configuration file.
    """

    REQUIRED_KEYS = ["building_constraints", "corridor_width", "rooms", "adjacency_requirements", "separation_requirements"]

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            first_char = file.read(1)
            if not first_char:
                return None, f"Configuration file is empty: {filepath}"
            file.seek(0)

            data = json.load(file)

            if not data:
                return None, f"JSON data is empty in file: {filepath}"

            for key in REQUIRED_KEYS:
                if key not in data:
                    return None, f"Missing required key '{key}' in file: {filepath}"
            
            return data, None

    except FileNotFoundError:
        return None, f"File not found at '{filepath}'"

    except json.JSONDecodeError:
        return None, f"Could not decode JSON from '{filepath}'."

    except Exception as e:
        return None, f"An unexpected error occurred while parsing '{filepath}': {e}"