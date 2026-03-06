import json
import os
import zones

def save_to_json(data, filename):
    """
    Save Python data to a JSON file.
    
    Args:
        data (dict | list): Data to save (must be JSON serializable).
        filename (str): Path to the JSON file.
    """
    # Validate filename
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("Filename must be a non-empty string.")
    
    # Validate data type
    if not isinstance(data, (dict, list)):
        raise TypeError("Data must be a dictionary or list to be JSON serializable.")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        
        # Write JSON to file with indentation for readability
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        
        print(f"Data successfully saved to '{filename}'")
    
    except (OSError, IOError) as e:
        print(f"Error saving file: {e}")
    except TypeError as e:
        print(f"Data is not JSON serializable: {e}")

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
    if False:
        data = zones.get_zone_data(15)

        locations: dict[str, tuple] = {}

        for name, zone_data in data.items():
            locations[name] = zone_data[2]

            # distances = {k: v for k, v in sorted(zone[1].items(), key=lambda x: zone[0][x[0]][0])}
            # journeys = zone[0]
        
        save_to_json(locations, "output/locations.json")
    else:
        locations: dict[str, dict[str, dict[str, tuple[float, float]]]] = read_json_file("output/locations.json")

        for mode in ["DRIVE", "BICYCLE", "WALK", "TWO_WHEELER", "BUS", "TRAIN"]:
            for name, zone_data in locations.items():
                size = 0
                mode_name = mode

                if mode in ["BUS", "TRAIN"]:
                    mode_name = "TRANSIT"
                    size = 10
                else:
                    size = 25

                zone_data = locations[name]

                total_num_origins = len(zone_data["origin"])
                total_num_destinations = len(zone_data["destination"])
                num_origins, num_destinations = 0, 0

                if total_num_origins < size:
                    num_origins = total_num_origins
                    num_destinations = (size * size) // total_num_origins
                elif total_num_destinations < size:
                    num_destinations = total_num_destinations
                    num_origins = (size * size) // total_num_destinations
                else:
                    num_origins = size
                    num_destinations = size

                if total_num_origins < num_origins:
                    num_origins = total_num_origins
                if total_num_destinations < num_destinations:
                    num_destinations = total_num_destinations

                for origins_start in range(0, total_num_origins, num_origins):
                    for destinations_start in range(0, total_num_destinations, num_destinations):
                        origins = []
                        destinations = []

                        origins_end = origins_start + num_origins
                        destinations_end = destinations_start + num_destinations

                        if origins_end > total_num_origins - 1:
                            origins_end = total_num_origins - 1

                        if destinations_end > total_num_destinations - 1:
                            destinations_end = total_num_destinations - 1

                        for location in list(zone_data["origin"].values())[:num_origins]:
                            origins.append({"waypoint": {"location": {"latLng": {"latitude": location[0], "longitude": location[1]}}}})

                        for location in list(zone_data["destination"].values())[:num_destinations]:
                            destinations.append({"waypoint": {"location": {"latLng": {"latitude": location[0], "longitude": location[1]}}}})

                        journey_data = {"origins": origins, "destinations": destinations, "travelMode": mode_name}
                        
                        if mode_name == "TRANSIT":
                            journey_data["transitPreferences"] = {"allowedTravelModes": [mode]}

                        save_to_json(journey_data, f"output/journeys/journeys_{name}_origins{origins_start}-{origins_end}_destinations{destinations_start}-{destinations_end}_{mode}.json")