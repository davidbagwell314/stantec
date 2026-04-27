# Script to analyse results
# For instance, use journey time and mode of transport to estimate carbon emissions

import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
import math
from scipy import stats
import csv
import os

# What data to visualise
RESULT_TYPE = 4

def get_journeys(remove_outliers: bool = False, msoa_journey: bool = True, residence_zones: list[str] = [], workplace_zones: list[str] = [], modes: list[str] = []) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Get distances and journey times for different journeys and modes of transport
    
    # remove_outliers: Whether to remove outliers (more than 2 standard deviations from mean) from analysis
    # msoa_journey: Whether the journey is between MSOAs or entire zones
    # residence_zones: Zones of residence to be analysed
    # workplace_zones: Zones of workplace to be analysed
    # modes: Modes of transport to be analysed

    # Returns 3 dataframes: all journeys, motorway journeys, and non-motorway journeys

    journeys = pd.read_csv('output/api_journeys.csv' if msoa_journey else 'output/zone_journeys.csv')

    # Criteria for the data we want to analyse

    # Filter journeys based on criteria
    filtered = journeys
    if len(residence_zones) > 0:
        filtered = filtered[filtered['zone_residence'].isin(residence_zones)]
    if len(workplace_zones) > 0:
        filtered = filtered[filtered['zone_workplace'].isin(workplace_zones)]
    if len(modes) > 0:
        filtered = filtered[filtered['mode'].isin(modes)]

    # Distances, journey times, and number of people for the filtered journeys
    frequencies: list[int] = list(filtered['number'])
    distances: list[float] = list(filtered['distance'])
    times: list[float] = list(filtered['time'])

    # Mean and standard deviation for distances and times
    dist_mean = np.mean(distances)
    time_mean = np.mean(times)
    dist_std = np.std(distances)
    time_std = np.std(times)

    # Remove outliers for better analysis
    if remove_outliers:
        filtered = filtered[(filtered['distance'] > dist_mean - 2 * dist_std) & (filtered['distance'] < dist_mean + 2 * dist_std) & (filtered['time'] > time_mean - 2 * time_std) & (filtered['time'] < time_mean + 2 * time_std)]

        # Update `frequencies`, `distances`, and `times`
        frequencies = list(filtered['number'])
        distances = list(filtered['distance'])
        times = list(filtered['time'])

        # Update mean and standard deviation to align with updated data
        dist_mean = np.mean(distances)
        time_mean = np.mean(times)
        dist_std = np.std(distances)
        time_std = np.std(times)

    # Zones without motorway journeys between them
    non_motorway_zones = {'taunton': ['wellington'], 'tiverton': ['exeter', 'cullompton']}

    # Convert the dictionary to a list for ease of use
    non_motorway_list: list[tuple[str, str]] = []
    for origin, destinations in non_motorway_zones.items():
        for destination in destinations:
            non_motorway_list.append((origin, destination))
            non_motorway_list.append((destination, origin))

    filtered['zone_journey'] = list(zip(filtered["zone_residence"], filtered["zone_workplace"]))

    motorway = filtered
    non_motorway = filtered

    return filtered, motorway, non_motorway

if __name__ == "__main__":
    match RESULT_TYPE:
        case 0:
            # TRA0308 estimated traffic counts

            traffic: pd.DataFrame = pd.read_csv("data/tra0308.csv", delimiter='\t')

            # Get columns in the format we want
            traffic['Time of Day'] = traffic['Time of Day'].str[:5]
            traffic['Weekday'] = traffic['Monday'] + traffic['Tuesday'] + traffic['Wednesday'] + traffic['Thursday'] + traffic['Friday']
            traffic['Weekend'] = traffic['Saturday'] + traffic['Sunday']
            traffic['Total'] = traffic['Weekday'] + traffic['Weekend']
            
            # Plot results
            plot = sns.histplot(data=traffic, x='Time of Day', weights='Weekday')
            plot.set_xticklabels(plot.get_xticklabels(), rotation=45)
            plt.show()

        case 1:
            # Highways England traffic counts
            # NOT COMPLETE - DON'T USE

            columns = {'Site Name': str, 'Report Date': str, 'Time Period Ending': str, 'Time Interval': int, '0 - 520 cm': float, '521  - 660 cm': float, '661 - 1160 cm': float, '1160+ cm': float, '0 - 10 mph': float, '11 - 15 mph': float, '16 - 20 mph': float, '21 - 25 mph': float, '26 - 30 mph': float, '31 - 35 mph': float, '36 - 40 mph': float, '41 - 45 mph': float, '46 - 50 mph': float, '51 - 55 mph': float, '56 - 60 mph': float, '61 - 70 mph': float, '71 - 80 mph': float, '80+ mph': float, 'Avg mph': float, 'Total Volume': float}
            traffic: pd.DataFrame = pd.read_csv("data/traffic-counts/*.csv", delimiter='\t')

            traffic['Time of Day'] = traffic['Time Period Ending'].str[:5]
            traffic['Weekday'] = traffic['Monday'] + traffic['Tuesday'] + traffic['Wednesday'] + traffic['Thursday'] + traffic['Friday']
            traffic['Weekend'] = traffic['Saturday'] + traffic['Sunday']
            traffic['Total'] = traffic['Weekday'] + traffic['Weekend']
            
            plot = sns.histplot(data=traffic, x='Time of Day', weights='Weekday')
            plot.set_xticklabels(plot.get_xticklabels(), rotation=45)
            plt.show()

            traffic = pd.concat(all_counts, ignore_index=True)
            traffic['Report Date'] = pd.to_datetime(traffic['Report Date'], format="%d/%m/%Y %H:%M:%S")
            traffic['Time Period Ending'] = pd.to_datetime(traffic['Time Period Ending'], format="%H:%M:%S")

            print(traffic.dtypes)
            print(traffic.head())
            print(traffic['Site Name'].unique())

            plot = sns.scatterplot(data=traffic, x='Time Period Ending', y='Total Volume')
            # plot = sns.histplot(data=traffic, x='Time of Day', weights='Total Volume')
            plot.set_xticklabels(plot.get_xticklabels(), rotation=45)

            plt.show()
        case 2:
            # Distance vs Time

            all_journeys, motorway_journeys, non_motorway_journeys = get_journeys(remove_outliers=True)

            sns.scatterplot(data=all_journeys, x="time", y = "distance", hue="mode", size="number", sizes=(1, 50))

            plt.title('Journey distance vs time')
            plt.xlabel('Time (s)')
            plt.ylabel('Distance (m)')

            plt.show()
        
        case 3:
            # Distribution of journey times ['driving', 'passenger', 'bus', 'train', 'taxi', 'metro']

            all_journeys, motorway_journeys, non_motorway_journeys = get_journeys(remove_outliers=True, modes=['foot'])

            sns.histplot(data=all_journeys, x="time", hue="mode", weights="number", bins=100, multiple="stack")

            plt.title('Distribution of journey times')
            plt.xlabel('Time (s)')
            plt.ylabel('Number')

            plt.show()
        
        case 4:
            # Data for binary logit model

            # Whether to remove outliers (more than 2 standard deviations from mean) from analysis
            REMOVE_OUTLIERS = True

            # Get distances and journey times for different journeys and modes of transport
            all_journeys, motorway_journeys, non_motorway_journeys = get_journeys(remove_outliers=True)

            car = all_journeys[all_journeys['mode'].isin(['driving', 'motorcycle', 'taxi'])]
            pt = all_journeys[all_journeys['mode'].isin(['bus', 'train', 'metro'])]
            other = all_journeys[all_journeys['mode'].isin(['passenger', 'bicycle', 'foot', 'other'])]

            results: list[list] = []
            proportions: list[list] = []

            org_dest: list[tuple[str, str, str, str]] = []

            for row in all_journeys.itertuples():
                route = (str(row.residence), str(row.workplace), str(row.zone_residence), str(row.zone_workplace))
                if route not in org_dest:
                    org_dest.append(route)

            for route in org_dest:
                if route[0] != route[1]:
                    this_car = car[(car['residence'] == route[0]) & (car['workplace'] == route[1])]
                    this_pt = pt[(pt['residence'] == route[0]) & (pt['workplace'] == route[1])]
                    this_other = other[(other['residence'] == route[0]) & (other['workplace'] == route[1])]

                    num_car = len(this_car)
                    num_pt = len(this_pt)
                    num_other = len(this_other)

                    zone_org = route[2]
                    zone_dest = route[3]

                    car_cost = 0.0
                    pt_cost = 0.0
                    other_cost = 0.0

                    car_total = 0
                    pt_total = 0
                    other_total = 0

                    for i in range(num_car):
                        car_row = tuple(this_car.iloc[i])

                        car_total += car_row[5]
                        car_cost += (car_row[7] / 60.0) * car_row[5]


                    for i in range(num_pt):
                        pt_row = tuple(this_pt.iloc[i])

                        pt_total += pt_row[5]
                        pt_cost += (pt_row[7] / 60.0) * pt_row[5]
                    
                    for i in range(num_other):
                        other_row = tuple(this_other.iloc[i])

                        other_total += other_row[5]
                        other_cost += (other_row[7] / 60.0) * other_row[5]

                    if pt_total > 0 and car_total > 0:
                        results.append([zone_org, zone_dest, pt_cost / pt_total, car_cost / car_total, pt_total, car_total, pt_total + car_total])
                        proportions.append([100.0 * pt_total / (pt_total + car_total)])
                    elif pt_total > 0:
                        results.append([zone_org, zone_dest, pt_cost / pt_total, 0.0, pt_total, car_total, pt_total + car_total])
                        proportions.append([100.0])
                    elif car_total > 0:
                        results.append([zone_org, zone_dest, 0.0, car_cost / car_total, pt_total, car_total, pt_total + car_total])
                        proportions.append([0.0])


            with open("output/logit.csv", mode='w', newline='') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerows(results)

            with open("output/proportions.csv", mode='w', newline='') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerows(proportions)

            #car.to_csv('output/logit.csv', index=False)

        case 5:
            # Initialise data for use later
            msoa_codes: list[str] = []
            zone_data: dict[str, gpd.GeoDataFrame] = {}

            # Read zone shapefiles
            for root, dirs, files in os.walk("GIS/shapes/"):
                for n in files:
                    name, extension = os.path.splitext(n)
                    if extension == ".shp":
                        fp = os.path.join(root, n)
                        zone_data[name] = gpd.read_file(fp)
                break

            # Process zone shapefiles
            for name, zone in zone_data.items():
                msoa_codes += zone['MSOA11CD'].to_list()
                if zone.crs is None or zone.crs.to_epsg() != 4326:
                    zone_data[name] = zone.to_crs(epsg=4326)

            pwc = gpd.read_file("GIS/shapes/MSOA_Dec_2011_PWC_in_England_and_Wales_2022_-4970423835205684272/MSOA_Dec_2011_PWC_in_England_and_Wales.shp")
            pwc = pwc[pwc['msoa11cd'].isin(msoa_codes)]

            stations = gpd.read_file("GIS/shapes/Bristol_Exeter_Railways/Bristol_Exeter_Railway_Stations.shp")
            if stations.crs is None or stations.crs.to_epsg() != 4326:
                stations = stations.set_crs(epsg=27700)
                stations = stations.to_crs(epsg=4326)

            for msoa in pwc.itertuples():
                min_dist = 0
                for station in stations.itertuples():
                    ...