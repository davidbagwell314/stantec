# Script to analyse results
# For instance, use journey time and mode of transport to estimate carbon emissions

import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import math
from scipy import stats

# Whether to remove outliers (more than 2 standard deviations from mean) from analysis
REMOVE_OUTLIERS = False

if __name__ == "__main__":
    # Get distances and journey times for different journeys and modes of transport
    api_journeys = pd.read_csv('output/api_journeys.csv')
    non_api_journeys = pd.read_csv('output/non_api_journeys.csv')
    journeys = pd.concat([df for df in [api_journeys] if not df.empty], axis=0)

    # Criteria for the data we want to analyse
    residence_zones: list[str] = []
    workplace_zones: list[str] = []
    modes: list[str] = ['train']

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
    
    split_line=[]
    for i in range (len(times)):
        split_line.append(7 * times[i] + 6600)

    non_motorway_x = []
    non_motorway_y = []
    motorway_x = []
    motorway_y = []
    for i in range (len(times)):
        if distances[i] < 7 * times[i] + 6600:
            non_motorway_x.append(times[i])
            non_motorway_y.append(distances[i])
        else:
            motorway_x.append(times[i])
            motorway_y.append(distances[i])
    
    # Calling linear regression assigning the output to the variables on the left of the equation 
    gradient, intercept,r,p,st_err = stats.linregress(non_motorway_x, non_motorway_y)
    #looping over the length of x and applying y=mx+c using the m and c from the output above to find the regression line   
    non_motorway_line=[]
    for i in range (len(non_motorway_x)):
        non_motorway_line.append(gradient * non_motorway_x[i] + intercept)

    # Calling linear regression assigning the output to the variables on the left of the equation 
    gradient, intercept,r,p,st_err = stats.linregress(motorway_x, motorway_y)
    #looping over the length of x and applying y=mx+c using the m and c from the output above to find the regression line   
    motorway_line=[]
    for i in range (len(motorway_x)):
        motorway_line.append(gradient * motorway_x[i] + intercept)

    # Plotting the data points and the best fit line and the error bars
    plt.scatter(times, distances)
    plt.plot(times, split_line)
    plt.plot(non_motorway_x, non_motorway_line)
    plt.plot(motorway_x, motorway_line)
    plt.title('Best fit line using regression method')
    plt.xlabel('Time (s)')
    plt.ylabel('Distance (m)')

    plt.show()
    print("Gradient:", gradient)
    
    # plt.hist(distances, bins=100, weights=frequencies)
    plt.savefig("graphs/histogram.png")