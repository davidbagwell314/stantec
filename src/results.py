import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

if __name__ == "__main__":
    api_journeys = pd.read_csv('output/api_journeys.csv')
    non_api_journeys = pd.read_csv('output/non_api_journeys.csv')
    journeys = pd.concat([df for df in [api_journeys, non_api_journeys] if not df.empty], axis=0)

    residence_zones: list[str] = []
    workplace_zones: list[str] = []
    modes: list[str] = []

    filtered = journeys
    if len(residence_zones) > 0:
        filtered = filtered[filtered['zone_residence'].isin(residence_zones)]
    if len(workplace_zones) > 0:
        filtered = filtered[filtered['zone_workplace'].isin(workplace_zones)]
    if len(modes) > 0:
        filtered = filtered[filtered['mode'].isin(modes)]

    distances: list[float] = list(filtered['distance'])
    times: list[float] = list(filtered['time'])

    dist_mean = np.mean(distances)
    time_mean = np.mean(times)

    dist_std = np.std(distances)
    time_std = np.std(times)

    filtered = filtered[(filtered['distance'] > dist_mean - 2 * dist_std) & (filtered['distance'] < dist_mean + 2 * dist_std) & (filtered['time'] > time_mean - 2 * time_std) & (filtered['time'] < time_mean + 2 * time_std)]

    frequencies = list(filtered['number'])
    distances = list(filtered['distance'])
    times = list(filtered['time'])

    #plt.scatter(times, distances)
    plt.hist(distances, bins=100, weights=frequencies)
    plt.savefig("graphs/histogram.png")