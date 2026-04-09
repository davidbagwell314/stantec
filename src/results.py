# Script to analyse results
# For instance, use journey time and mode of transport to estimate carbon emissions

import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
import math
from scipy import stats
import csv
import os

if __name__ == "__main__":
    if True:
        columns = {'Site Name': str, 'Report Date': str, 'Time Period Ending': str, 'Time Interval': int, '0 - 520 cm': float, '521  - 660 cm': float, '661 - 1160 cm': float, '1160+ cm': float, '0 - 10 mph': float, '11 - 15 mph': float, '16 - 20 mph': float, '21 - 25 mph': float, '26 - 30 mph': float, '31 - 35 mph': float, '36 - 40 mph': float, '41 - 45 mph': float, '46 - 50 mph': float, '51 - 55 mph': float, '56 - 60 mph': float, '61 - 70 mph': float, '71 - 80 mph': float, '80+ mph': float, 'Avg mph': float, 'Total Volume': float}
        traffic: pd.DataFrame = pd.read_csv("data/tra0308.csv", delimiter='\t')

        traffic['Time of Day'] = traffic['Time of Day'].str[:5]
        traffic['Weekday'] = traffic['Monday'] + traffic['Tuesday'] + traffic['Wednesday'] + traffic['Thursday'] + traffic['Friday']
        traffic['Weekend'] = traffic['Saturday'] + traffic['Sunday']
        traffic['Total'] = traffic['Weekday'] + traffic['Weekend']
        
        plot = sns.histplot(data=traffic, x='Time of Day', weights='Weekday')
        plot.set_xticklabels(plot.get_xticklabels(), rotation=45)
        plt.show()

        """traffic = pd.concat(all_counts, ignore_index=True)
        traffic['Report Date'] = pd.to_datetime(traffic['Report Date'], format="%d/%m/%Y %H:%M:%S")
        traffic['Time Period Ending'] = pd.to_datetime(traffic['Time Period Ending'], format="%H:%M:%S")

        print(traffic.dtypes)
        print(traffic.head())
        print(traffic['Site Name'].unique())

        sns.scatterplot(data=traffic, x='Time Period Ending', y='Total Volume')

        #sns.histplot(data=traffic, x='Time Period Ending', weights='Total Volume', bins=24, binwidth=1)"""

        plt.show()
    else:
        # Whether to remove outliers (more than 2 standard deviations from mean) from analysis
        REMOVE_OUTLIERS = True

        # Whether the journey is between MSOAs or entire zones
        MSOA_JOURNEY = True

        # Get distances and journey times for different journeys and modes of transport
        journeys = pd.read_csv('output/api_journeys.csv' if MSOA_JOURNEY else 'output/zone_journeys.csv')

        # Criteria for the data we want to analyse
        residence_zones: list[str] = []
        workplace_zones: list[str] = []
        modes: list[str] = ['driving', 'passenger', 'bus', 'train', 'taxi', 'metro']

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
        if REMOVE_OUTLIERS:
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

        """# Plot results 
        gradient, intercept,r,p,st_err = stats.linregress(times, distances)
        line = [(gradient * time + intercept) for time in times]
        print(f"Mean speed: {gradient / 1600.0 * 3600.0}mph")

        non_motorway_dump = {'taunton': ['wellington'], 'tiverton': ['exeter', 'cullompton']}
        non_motorway: list[tuple[str, str]] = []
        for origin, destinations in non_motorway_dump.items():
            for destination in destinations:
                non_motorway.append((origin, destination))
                non_motorway.append((destination, origin))

        # non_motorway: list[tuple[str, str]] = [('taunton', 'wellington'), ('wellington', 'taunton')]

        filtered['zone_journey'] = list(zip(filtered["zone_residence"], filtered["zone_workplace"]))

        # Plotting the data points and the best fit line and the error bars
        # sns.regplot(data=filtered, x="time", y = "distance")
        #sns.scatterplot(data=filtered, x="time", y = "distance", hue=((filtered["zone_residence"] == filtered["zone_workplace"]) | filtered['zone_journey'].isin(non_motorway)))
        sns.scatterplot(data=filtered, x="time", y = "distance", hue="mode")
        #plt.scatter(times, distances)
        #plt.plot(times, line)
        #plt.title('Journey distance vs time')
        #plt.xlabel('Time (s)')
        #plt.ylabel('Distance (m)')

        plt.show()
        
        # plt.hist(distances, bins=100, weights=frequencies)
        #plt.savefig("graphs/histogram.png")"""
        
        car = filtered[filtered['mode'].isin(['driving', 'motorcycle', 'taxi'])]
        pt = filtered[filtered['mode'].isin(['bus', 'train', 'metro'])]
        other = filtered[filtered['mode'].isin(['passenger', 'bicycle', 'foot', 'other'])]

        results: list[list] = []
        proportions: list[list] = []

        org_dest: list[tuple[str, str, str, str]] = []

        for row in filtered.itertuples():
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
                    car_cost += car_row[7] / 60.0
                
                for i in range(num_car):
                    car_row = tuple(this_car.iloc[i])

                    car_total += car_row[5]
                    car_cost += car_row[7] / 60.0

                for i in range(num_pt):
                    pt_row = tuple(this_pt.iloc[i])

                    pt_total += pt_row[5]
                    pt_cost += pt_row[7] / 60.0
                
                for i in range(num_other):
                    other_row = tuple(this_other.iloc[i])

                    other_total += other_row[5]
                    other_cost += other_row[7] / 60.0

                if num_pt > 0 and num_car > 0:
                    results.append([zone_org, zone_dest, pt_cost / num_pt, car_cost / num_car])
                    proportions.append([100.0 * pt_total / (pt_total + car_total)])
                elif num_pt > 0:
                    results.append([zone_org, zone_dest, pt_cost / num_pt, 0.0])
                    proportions.append([100.0])
                elif num_car > 0:
                    results.append([zone_org, zone_dest, 0.0, car_cost / num_car])
                    proportions.append([0.0])


        with open("output/logit.csv", mode='w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(results)

        with open("output/proportions.csv", mode='w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(proportions)

        #car.to_csv('output/logit.csv', index=False)
