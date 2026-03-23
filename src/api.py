# Script to process Google Maps API responses
# Writes data to `output\api_journeys.csv` so we can use it in `results.py`

import json
import os
import pandas as pd
import csv
import zones

# Reads data from json file
# Used for reading responses from Google Maps API
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
    # Whether to use zone journeys or MSOA journeys
    if True:
        # Origin and destination indices for each element returned from Google Maps API
        # Each element has an origin and destination index, but these don't specify what the MSOA codes are
        # Storing an index fixes that issue
        all_journeys_idx = pd.read_csv("output/api_journeys_idx.csv")

        # Get table of zones
        zone_tables = zones.get_zones()

        # Dictionary of MSOA codes for each zone
        zone_codes: dict[str, list[str]] = {}

        # Iterate through each zone
        for name, zone_table in zone_tables.items():
            zone_codes[name] = []
            
            # Fetch MSOA codes for this zone
            for zone in zone_table.itertuples():
                zone_codes[name].append(str(zone.MSOA11CD))

        # wu03ew modes of transport
        # wu03ew columns: residence, workplace, all, home, metro, train, bus, taxi, motorcycle, driving, passenger, bicycle, foot, other
        wu03ew_modes = ["all", "home", "metro", "train", "bus", "taxi", "motorcycle", "driving", "passenger", "bicycle", "foot", "other"]

        # Get wu03ew table
        wu03ew: dict[tuple[str, str], tuple] = {}
        wu03ew_table = pd.read_csv("data/wu03ew_v2.csv")

        # Get wu03ew data in dictionary format
        for wu03ew_row in wu03ew_table.itertuples(index=False):
            row_data = tuple([int(str(x)) for i, x in enumerate(wu03ew_row) if i > 1])

            # Check if there are any journeys
            if row_data[0] > 0:
                wu03ew[(str(wu03ew_row[0]), str(wu03ew_row[1]))] = row_data

        # Google Maps API modes of transport and their columns in the wu03ew table
        modes: dict[str, list[int]] = {"DRIVE": [5, 7, 8], "BICYCLE": [9], "WALK": [10], "TWO_WHEELER": [6], "BUS": [4], "TRAIN": [3]}

        # Origin and destination indices of each MSOA by MSOA code, mode of transport, and zone
        origins_idx: dict[str, dict[str, dict[int, str]]] = {}
        destinations_idx: dict[str, dict[str, dict[int, str]]] = {}

        # Add all the indices to the two dictionaries
        # Iterate through each zone
        for name in zone_codes.keys():
            origins_idx[name] = {}
            destinations_idx[name] = {}

            # Iterate through each mode of transport
            for mode in modes.keys():
                origins_idx[name][mode] = {}
                destinations_idx[name][mode] = {}

                # Get all the indices for this zone and mode of transport
                journeys_idx = all_journeys_idx[(all_journeys_idx['zone'] == name) & (all_journeys_idx['mode'] == mode)]
                
                # Iterate through each index and add it to the dictionaries
                for row in journeys_idx.itertuples():
                    origins_idx[name][mode][int(str(row.originIndex))] = str(row.residence)
                    destinations_idx[name][mode][int(str(row.destinationIndex))] = str(row.workplace)

        # Column names
        journey_data: list[list] = [['zone_residence', 'zone_workplace', 'mode', 'residence', 'workplace', 'number', 'distance', 'time']]

        responses_location: str = "output/responses/"

        # Read through each response
        for root, dirs, files in os.walk(responses_location):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                print(file_path)

                # Use filename to get information about response
                info: list[str] = file_name.split('.json')
                info = info[0].split("journeys_")
                info = info[1].split("_origins")
                info = info[:1] + info[1].split("_destinations")
                info = info[:2] + info[2].split("_")

                # Zone, mode of transport, range of origin indices, range of destination indices
                name = info[0]
                mode = info[3]
                if mode == "TWO":
                    mode = info[3] + "_" + info[4]
                origins = [int(x) for x in info[1].split("-")]
                destinations = [int(x) for x in info[2].split("-")]

                # Read data for this response
                data: list[dict] = read_json_file(file_path)
                
                for element in data:
                    # Origin and destination indices
                    origin: int = element['originIndex'] + origins[0]
                    dest: int = element['destinationIndex'] + destinations[0]

                    print(origin, dest, element['destinationIndex'])

                    try:
                        # Get the origins and destination MSOA codes using their indices
                        journey: tuple[str, str] = (origins_idx[name][mode][origin], destinations_idx[name][mode][dest])
                    except:
                        ...
                    # Find the workplace zone
                    # "other" is a fallback in case the workplace is not in one of our zones
                    workplace = "other"
                    for workplace_name, codes in zone_codes.items():
                        if journey[1] in codes:
                            workplace = workplace_name
                            break

                    # Iterate through each wu03ew mode of transport for the Google Maps API mode of transport
                    if journey in wu03ew:
                        for column in modes[mode]:
                            number = wu03ew[journey][column]

                            # Check if there are any journeys
                            if number > 0:
                                try:
                                    journey_data.append([name, workplace, wu03ew_modes[column], journey[0], journey[1], number, element['distanceMeters'], int(element['duration'][:-1])])
                                except:
                                    journey_data.append([name, workplace, wu03ew_modes[column], journey[0], journey[1], number, 0, 0])
                    
        # Save the data
        with open('output/api_journeys.csv', 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(journey_data)
    else:
        # Dictionary to map MSOA code to zone name
        zone_names: dict[str, str] = {}

        zone_tables = zones.get_zones()

        for name, zone in zone_tables.items():
            for row in zone.itertuples(index=False):
                zone_names[str(row.MSOA11CD)] = name

        # wu03ew modes of transport
        # wu03ew columns: residence, workplace, all, home, metro, train, bus, taxi, motorcycle, driving, passenger, bicycle, foot, other
        wu03ew_modes = ["all", "home", "metro", "train", "bus", "taxi", "motorcycle", "driving", "passenger", "bicycle", "foot", "other"]

        # Get wu03ew table
        wu03ew: dict[tuple[str, str], tuple] = {}
        wu03ew_table = pd.read_csv("data/wu03ew_v2.csv")

        # Get wu03ew data in dictionary format
        for wu03ew_row in wu03ew_table.itertuples(index=False):
            row_data = tuple([int(str(x)) for i, x in enumerate(wu03ew_row) if i > 1])

            # Check if there are any journeys
            if row_data[0] > 0:
                # Get the zones which this journey is between
                origin_name = str(wu03ew_row[0])
                destination_name = str(wu03ew_row[1])

                if origin_name in zone_names:
                    origin_name = zone_names[origin_name]
                    
                    if destination_name in zone_names:
                        destination_name = zone_names[destination_name]
                    else:
                        destination_name = "other"

                    zone_journey = (origin_name, destination_name)

                    # Update wu03ew by number of people travelling between these zones
                    if not zone_journey in wu03ew:
                        wu03ew[zone_journey] = row_data
                    else:
                        new_journey = []
                        for i in range(len(row_data)):
                            new_journey.append(wu03ew[zone_journey][i] + row_data[i])
                        wu03ew[zone_journey] = tuple(new_journey)

        # Google Maps API modes of transport and their columns in the wu03ew table
        modes: dict[str, list[int]] = {"DRIVE": [5, 7, 8], "BICYCLE": [9], "WALK": [10], "TWO_WHEELER": [6], "BUS": [4], "TRAIN": [3]}

        # Column names
        journey_data: list[list] = [['zone_residence', 'zone_workplace', 'mode', 'number', 'distance', 'time']]

        responses_location: str = "output/responses/"

        # Read through each response
        for root, dirs, files in os.walk(responses_location):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                # Use filename to get information about response
                info: list[str] = file_name.split('.json')
                info = info[0].split("journeys_")

                mode = info[1]

                # Read data for this response
                data: list[dict] = read_json_file(file_path)
                
                for element in data:
                    # Origin and destination indices
                    origin: int = element['originIndex']
                    dest: int = element['destinationIndex']

                    # Get the origins and destination MSOA codes using their indices
                    journey: tuple[str, str] = (list(zone_tables.keys())[origin], list(zone_tables.keys())[dest])

                    # Iterate through each wu03ew mode of transport for the Google Maps API mode of transport
                    if journey in wu03ew:
                        for column in modes[mode]:
                            number = wu03ew[journey][column]
                            try:
                                journey_data.append([journey[0], journey[1], wu03ew_modes[column], number, element['distanceMeters'], int(element['duration'][:-1])])
                            except:
                                journey_data.append([journey[0], journey[1], wu03ew_modes[column], number, 0, 0])
                    
        # Save the data
        with open('output/zone_journeys.csv', 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(journey_data)