import json
import os
import pandas as pd
import csv
import zones

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

if __name__ == "__main__":
    all_journeys_idx = pd.read_csv("output/api_journeys_idx.csv")
    zone_tables = zones.get_zones()
    zone_codes: dict[str, list[str]] = {}
    for name, zone_table in zone_tables.items():
        zone_codes[name] = []
        for zone in zone_table.itertuples():
            zone_codes[name].append(str(zone.MSOA11CD))

    # wu03ew modes of transport
    # wu03ew columns: residence, workplace, all, home, metro, train, bus, taxi, motorcycle, driving, passenger, bicycle, foot, other
    wu03ew_modes = ["all", "home", "metro", "train", "bus", "taxi", "motorcycle", "driving", "passenger", "bicycle", "foot", "other"]

    # get wu03ew table
    wu03ew: dict[tuple[str, str], tuple] = {}
    wu03ew_table = pd.read_csv("data/wu03ew_v2.csv")

    for wu03ew_row in wu03ew_table.itertuples(index=False):
        row_data = tuple([int(str(x)) for i, x in enumerate(wu03ew_row) if i > 1])
        if row_data[0] > 0:
            wu03ew[(str(wu03ew_row[0]), str(wu03ew_row[1]))] = row_data

    # Google Maps API modes of transport and their columns in the wu03ew table
    modes: dict[str, list[int]] = {"DRIVE": [5, 7, 8], "BICYCLE": [9], "WALK": [10], "TWO_WHEELER": [6], "BUS": [4], "TRAIN": [3]}

    origins_idx: dict[str, dict[str, dict[int, str]]] = {}
    destinations_idx: dict[str, dict[str, dict[int, str]]] = {}

    for name in zone_codes.keys():
        origins_idx[name] = {}
        destinations_idx[name] = {}

        for mode in modes.keys():
            origins_idx[name][mode] = {}
            destinations_idx[name][mode] = {}

            journeys_idx = all_journeys_idx[(all_journeys_idx['zone'] == name) & (all_journeys_idx['mode'] == mode)]
            
            for row in journeys_idx.itertuples():
                origins_idx[name][mode][int(str(row.originIndex))] = str(row.residence)
                destinations_idx[name][mode][int(str(row.destinationIndex))] = str(row.workplace)

    compute_route_matrix_response_data: list[list] = [['zone_residence', 'zone_workplace', 'mode', 'residence', 'workplace', 'number', 'distance', 'time']]

    responses_location: str = "output/responses/"
    for root, dirs, files in os.walk(responses_location):
        for file_name in files:
            file_path = os.path.join(root, file_name)

            # use filename to get information about response
            info: list[str] = file_name.split('.json')
            info = info[0].split("journeys_")
            info = info[1].split("_origins")
            info = info[:1] + info[1].split("_destinations")
            info = info[:2] + info[2].split("_")
            name = info[0]
            mode = info[3]
            origins = [int(x) for x in info[1].split("-")]
            destinations = [int(x) for x in info[2].split("-")]

            data: list[dict] = read_json_file(file_path)
            
            for element in data:
                origin: int = element['originIndex'] + origins[0]
                dest: int = element['destinationIndex'] + destinations[0]
                journey: tuple[str, str] = (origins_idx[name][mode][origin], destinations_idx[name][mode][dest])
                workplace = "other"
                for workplace_name, codes in zone_codes.items():
                    if journey[1] in codes:
                        workplace = workplace_name
                        break

                for column in modes[mode]:
                    number = wu03ew[journey][column]
                    if number > 0:
                        compute_route_matrix_response_data.append([name, workplace, wu03ew_modes[column], journey[0], journey[1], number, element['distanceMeters'], int(element['duration'][:-1])])

    # Save the data
    with open('output/api_journeys.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(compute_route_matrix_response_data)