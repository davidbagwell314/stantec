# Script to analyse results
# For instance, use journey time and mode of transport to estimate carbon emissions

import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import numpy as np
import math
from scipy import stats

# Whether to remove outliers (more than 2 standard deviations from mean) from analysis
REMOVE_OUTLIERS = True

# Whether the journey is between MSOAs or entire zones
MSOA_JOURNEY = True

if __name__ == "__main__":
    # Get distances and journey times for different journeys and modes of transport
    journeys = pd.read_csv('output/api_journeys.csv' if MSOA_JOURNEY else 'output/zone_journeys.csv')

    # Criteria for the data we want to analyse
    residence_zones: list[str] = []
    workplace_zones: list[str] = []
    modes: list[str] = ['driving']

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

    # Plot results 
    gradient, intercept,r,p,st_err = stats.linregress(times, distances)
    line = [(gradient * time + intercept) for time in times]
    print(f"Mean speed: {gradient / 1600.0 * 3600.0}mph")

    # Plotting the data points and the best fit line and the error bars
    sns.scatterplot(data=filtered, x="time", y = "distance", hue="zone_workplace")
    #plt.scatter(times, distances)
    #plt.plot(times, line)
    #plt.title('Journey distance vs time')
    #plt.xlabel('Time (s)')
    #plt.ylabel('Distance (m)')

    plt.show()
    
    # plt.hist(distances, bins=100, weights=frequencies)
    #plt.savefig("graphs/histogram.png")