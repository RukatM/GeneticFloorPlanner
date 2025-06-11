import json


def parse_input_file(filepath):
    """
    Loads and parses a JSON configuration file.
    """

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            # TODO validation
            data = json.load(file)
            return data

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}.")
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
