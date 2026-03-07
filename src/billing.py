import json
import os

def read_json_file(file_path):
    """
    Reads and parses a JSON file.
    
    :param file_path: Path to the JSON file
    :return: Parsed Python object (dict/list) or None if error occurs
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)  # Parse JSON into Python object
            return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format. {e}")
    except PermissionError:
        print(f"Error: Permission denied when reading '{file_path}'.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None

if __name__ == "__main__":
    elements = 0
    directory = "output/journeys/"
    for root, dirs, files in os.walk(directory):
        for file in files:
            filename = str(os.path.join(root, file))
            data: dict[str, list | str] = read_json_file(filename)
            elements += len(data["origins"]) * len(data["destinations"])

    cost = 0.0
    if elements > 10000:
        cost += 5.0 * (elements - 10000) / 1000
    cost *= 100
    cost -= 0.00000001
    cost = str(int(cost))
    if len(cost) < 2:
        cost = "00" + cost
    elif len(cost) < 3:
        cost = "0" + cost
    
    print(f"Elements: {elements}")
    print(f"Cost: £{cost[:-2]}.{cost[-2:]}")
