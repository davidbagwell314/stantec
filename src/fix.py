# Program to fix the results from Google Maps API
# Some of the zones weren't correctly identified and the CSV file isn't in an optimal format
# This program should fix some of these issues

import pandas as pd
import zones

if __name__ == "__main__":
    # Get the journeys from `output/api_journeys.csv`
    journeys = pd.read_csv('output/api_journeys.csv')

    # Get the origin and destination MSOAs for each journey
    origins = journeys["residence"].to_list()
    destinations = journeys["workplace"].to_list()

    # Get every unique MSOA
    codes = list(set(origins + destinations))

    # Dictionary to map MSOA code to zone name
    zone_name: dict[str, str] = {}

    zone_data = zones.get_zones()

    for name, zone in zone_data.items():
        for row in zone.itertuples(index=False):
            zone_name[str(row.MSOA11CD)] = name

    for journey in journeys.itertuples(index=False):
        MSOA_residence = str(journey.residence)
        MSOA_workplace = str(journey.workplace)
        zone_residence = "other"
        zone_workplace = "other"

        if MSOA_residence in zone_name:
            zone_residence = zone_name[MSOA_residence]

        if MSOA_workplace in zone_name:
            zone_workplace = zone_name[MSOA_workplace]

        new_journey = (zone_residence, zone_workplace) + journey[2:]
        print(new_journey)