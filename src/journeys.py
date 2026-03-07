import json
import os
import csv
import zones

# saves data to json file
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

# reads data from json file
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

# retrieve both API and non-API journeys as well as other metadata, and save API journeys in correct format
def get_journeys(min_num_journeys: int, api_num_journeys: int, modes: dict[str, tuple[list[int], float]], save_location: str) -> tuple[dict[str, dict[str, dict[str, dict[str, tuple[float, float]]]]], dict[str, dict[str, dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]]]], dict[str, list[str]],  dict[tuple[float, float], str]]:
    data = zones.get_zone_data(min_num_journeys)

    zone_codes: dict[str, list[str]] = {}
    location_to_code: dict[tuple[float, float], str] = {}

    # Representation of journeys both with and without Google Maps API
    api_journeys: dict[str, dict[str, dict[str, dict[str, tuple[float, float]]]]] = {}
    non_api_journeys: dict[str, dict[str, dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]]]] = {}

    for name, zone_data in data.items():
        zone_codes[name] = zone_data[3]

        api_journeys[name] = {}
        non_api_journeys[name] = {}

        for mode, idx in modes.items():
            api_journeys[name][mode] = {"origin": {}, "destination": {}}
            non_api_journeys[name][mode] = {}

            for journey, people in zone_data[0].items():
                if journey[0] in zone_data[2] and journey[1] in zone_data[2]:
                    # check if enough people are doing the journey by this mode of transport
                    valid_api_journey = False
                    valid_journey = False
                    for i in idx[0]: # check for each column in wu03ew
                        if people[i] >= api_num_journeys:
                            valid_api_journey = True
                            break

                    if not valid_api_journey:
                        for i in idx[0]:
                            if people[i] >= min_num_journeys:
                                valid_journey = True
                                break

                    # add location/distance data for this mode of transport
                    if valid_api_journey:
                        api_journeys[name][mode]["origin"][journey[0]] = zone_data[2][journey[0]]
                        api_journeys[name][mode]["destination"][journey[1]] = zone_data[2][journey[1]]
                    elif valid_journey:
                        print(f"{journey}: {zone_data[1][journey]}")
                        non_api_journeys[name][mode][journey] = zone_data[1][journey]
                    
                    location_to_code[zone_data[2][journey[0]]] = journey[0]
                    location_to_code[zone_data[2][journey[1]]] = journey[1]

    # Save journeys in appropriate JSON format for Google Maps API
    for name, zone_data in api_journeys.items():
        for mode, data in zone_data.items():
            size = 0
            mode_name = mode

            # The API has a maximum number of elements (origins x destinations) it can process at a time
            # Therefore journeys should be grouped into blocks
            # Specify the base number of origins and destinations for these blocks
            if mode in ["BUS", "TRAIN"]:
                mode_name = "TRANSIT"
                size = 10
            else:
                size = 25

            # Number of origins and destinations
            total_num_origins = len(data["origin"])
            total_num_destinations = len(data["destination"])

            if total_num_origins > 0 and total_num_destinations > 0:
                # Get actual number of origins and destinations for each block
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

                # Iterate through each block
                for origins_start in range(0, total_num_origins, num_origins):
                    for destinations_start in range(0, total_num_destinations, num_destinations):
                        origins = []
                        destinations = []

                        # Endpoints of the origins and destinations for each block
                        origins_end = origins_start + num_origins
                        destinations_end = destinations_start + num_destinations

                        if origins_end > total_num_origins - 1:
                            origins_end = total_num_origins - 1

                        if destinations_end > total_num_destinations - 1:
                            destinations_end = total_num_destinations - 1

                        # Store origins
                        for location in list(data["origin"].values())[:num_origins]:
                            origins.append({"waypoint": {"location": {"latLng": {"latitude": location[0], "longitude": location[1]}}}})

                        # Store destinations
                        for location in list(data["destination"].values())[:num_destinations]:
                            destinations.append({"waypoint": {"location": {"latLng": {"latitude": location[0], "longitude": location[1]}}}})

                        journey_data = {"origins": origins, "destinations": destinations, "travelMode": mode_name}
                        
                        # Additional data for TRANSIT modes (BUS and TRAIN)
                        if mode_name == "TRANSIT":
                            journey_data["transitPreferences"] = {"allowedTravelModes": [mode]}

                        # Save data for use by Google Maps API
                        filepath = os.path.join(save_location, f"journeys_{name}_origins{origins_start}-{origins_end}_destinations{destinations_start}-{destinations_end}_{mode}.json")
                        save_to_json(journey_data, filepath)

    return api_journeys, non_api_journeys, zone_codes, location_to_code

if __name__ == "__main__":
    # Modes of transport and their columns in the wu03ew table
    modes: dict[str, tuple[list[int], float]] = {"DRIVE": ([5, 7, 8], 25.0), "BICYCLE": ([9], 6.0), "WALK": ([10], 1.4), "TWO_WHEELER": ([6], 17.0), "BUS": ([4], 5.5), "TRAIN": ([3], 30.0)}

    api_journeys, non_api_journeys, zone_codes, location_to_code = get_journeys(5, 50, modes, "output/journeys/")

    csv_data: list[list] = [['zone', 'mode', 'residence', 'workplace', 'distance', 'time']]

    non_api_dist_time: dict[str, dict[str, dict[tuple[str, str], tuple[float, float]]]] = {}
    for name, zone_data in non_api_journeys.items():
        non_api_dist_time[name] = {}
        for mode, data in zone_data.items():
            non_api_dist_time[name][mode] = {}
            for journey, distance in data.items():
                journey_dist = distance[2] * 1.2
                journey_time = journey_dist / modes[mode][1]
                non_api_dist_time[name][mode][journey] = (journey_dist, journey_time)
                csv_data.append([name, mode, journey[0], journey[1], journey_dist, journey_time])

    with open('output/non_api_journeys.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(csv_data)