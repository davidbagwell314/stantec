import json
import os
import csv
import zones

# Saves data to json file
# Used for storing data in format for Google Maps API
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

# retrieve both API and non-API journeys as well as other metadata, and save API journeys in correct format
def get_journeys(min_num_journeys: int, api_num_journeys: int, modes: dict[str, tuple[list[int], float]], save_location: str) -> tuple[dict[str, dict[str, dict[str, dict[str, tuple[float, float]]]]], dict[str, dict[str, dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]]]], dict[str, list[str]],  dict[tuple[float, float], str], dict[int, dict[tuple[str, str], int]]]:
    data = zones.get_zone_data(min_num_journeys)
    wu03ew: dict[int, dict[tuple[str, str], int]] = {}

    zone_codes: dict[str, list[str]] = {}
    location_to_code: dict[tuple[float, float], str] = {}

    # Representation of journeys both with and without Google Maps API
    api_journeys: dict[str, dict[str, dict[str, dict[str, tuple[float, float]]]]] = {}
    non_api_journeys: dict[str, dict[str, dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]]]] = {}

    # Iterate through each zone
    for name, zone_data in data.items():
        zone_codes[name] = zone_data[3]

        api_journeys[name] = {}
        non_api_journeys[name] = {}

        # Iterate through each mode of transport
        for mode, idx in modes.items():
            api_journeys[name][mode] = {"origin": {}, "destination": {}}
            non_api_journeys[name][mode] = {}

            # Iterate through each journey for this mode of transport in this zone
            # `people` represents the number of people for each mode of transport
            for journey, people in zone_data[0].items():
                # Check if these journeys are to and from an MSOA with a known location
                if journey[0] in zone_data[2] and journey[1] in zone_data[2]:
                    # Check if enough people are doing the journey by this mode of transport
                    valid_api_journey = False
                    valid_journey = False
                    for i in idx[0]: # check for each column in wu03ew
                        num = people[i]

                        # Get wu03ew data
                        if not i in wu03ew:
                            wu03ew[i] = {}
                        if not journey in wu03ew[i]:
                            wu03ew[i][journey] = 0
                        wu03ew[i][journey] += num

                        if num >= api_num_journeys:
                            valid_api_journey = True

                    # Not enough journeys to use Google Maps API
                    # Could still be enough journeys for estimates
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
                        non_api_journeys[name][mode][journey] = zone_data[1][journey]
                    
                    location_to_code[zone_data[2][journey[0]]] = journey[0]
                    location_to_code[zone_data[2][journey[1]]] = journey[1]

    # Save journeys in appropriate JSON format for Google Maps API
    for name, zone_data in api_journeys.items():
        for mode, data in zone_data.items():
            size = 0
            mode_name = mode

            # The API has a maximum number of elements (origins x destinations) it can process at a time
            # Therefore journeys should be grouped into blocks of either 625 or 100 elements
            # Specify the base number of origins and destinations for these blocks
            if mode in ["BUS", "TRAIN"]:
                mode_name = "TRANSIT"
                size = 10
            else:
                size = 25

            # Number of origins and destinations
            total_num_origins = len(data["origin"])
            total_num_destinations = len(data["destination"])

            # Ensure there are actually any journeys... no point processing non-existent journeys
            if total_num_origins > 0 and total_num_destinations > 0:
                # Get actual number of origins and destinations for each block
                # Number of elements (origins x destinations) should not exceed the maximum
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

    return api_journeys, non_api_journeys, zone_codes, location_to_code, wu03ew

if __name__ == "__main__":
    # wu03ew modes of transport
    # wu03ew columns: residence, workplace, all, home, metro, train, bus, taxi, motorcycle, driving, passenger, bicycle, foot, other
    wu03ew_modes = ["all", "home", "metro", "train", "bus", "taxi", "motorcycle", "driving", "passenger", "bicycle", "foot", "other"]

    # Google Maps API modes of transport and their columns in the wu03ew table and their estimated speeds
    # Multiple wu03ew modes of transport may be the same Google Maps API mode of transport - e.g. taxi, driving, and passenger are all DRIVE
    # Speeds are estimated from Google Maps API responses - update these numbers for more accurate results
    modes: dict[str, tuple[list[int], float]] = {"DRIVE": ([5, 7, 8], 25.0), "BICYCLE": ([9], 6.0), "WALK": ([10], 1.4), "TWO_WHEELER": ([6], 17.0), "BUS": ([4], 5.5), "TRAIN": ([3], 30.0)}

    api_journeys, non_api_journeys, zone_codes, location_to_code, wu03ew = get_journeys(5, 5, modes, "output/journeys/")

    # columns to be used
    api_journeys_idx_data: list[list] = [['zone', 'mode', 'residence', 'workplace', 'originIndex', 'destinationIndex']]
    non_api_journeys_data: list[list] = [['zone_residence', 'zone_workplace', 'mode', 'residence', 'workplace', 'number', 'distance', 'time']]

    # Store the indices for origins and destinations for journeys using Google Maps API
    # These will be processed by `api.py`
    for name, zone_data in api_journeys.items():
        for mode, data in zone_data.items():
            for i, origin in enumerate(data["origin"].keys()):
                for j, destination in enumerate(data["destination"].keys()):
                    api_journeys_idx_data.append([name, mode, origin, destination, i, j])

    # Save the data
    with open('output/api_journeys_idx.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(api_journeys_idx_data)

    # Estimate distance and journey time for journeys not using Google Maps API
    non_api_dist_time: dict[str, dict[str, dict[tuple[str, str], tuple[float, float]]]] = {}

    # Iterate through each zone
    for name, zone_data in non_api_journeys.items():
        non_api_dist_time[name] = {}

        # Iterate through each mode of transport
        for mode, data in zone_data.items():
            non_api_dist_time[name][mode] = {}

            # Iterate through each journey
            for journey, distance in data.items():
                # Actual journey distance will be slightly longer than straight-line distance
                # Calculate this factor based on Google Maps API responses
                journey_dist = distance[2] * 1.2

                # Time = distance / speed
                journey_time = journey_dist / modes[mode][1]

                non_api_dist_time[name][mode][journey] = (journey_dist, journey_time)

                # Find the workplace zone
                # "other" is a fallback in case the workplace is not in one of our zones
                workplace = "other"
                for workplace_name, codes in zone_codes.items():
                    if journey[1] in codes:
                        workplace = workplace_name
                        break
                
                # Iterate through each wu03ew mode of transport for the Google Maps API mode of transport
                for column in modes[mode][0]:
                    # Check if there are any journeys
                    if wu03ew[column][journey] > 0:
                        non_api_journeys_data.append([name, workplace, wu03ew_modes[column], journey[0], journey[1], wu03ew[column][journey], journey_dist, journey_time])

    # Save the data
    with open('output/non_api_journeys.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(non_api_journeys_data)