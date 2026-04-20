# Script to display maps
# I.e. if there's anything geographical we want to represent

import os
import pandas as pd
import geopandas as gpd
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib import cm, colors, patches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import shapely
import numpy as np
import math

# Name of plot
PLOT_NAME = "map6"

# Whether to process/render each layer
ALL_MSOA_BOUNDARIES = True
ZONE_MSOA = True
ZONE_MSOA_PWC = True
TRANSPORT = True
ZONE_COLOURS = False
JOURNEYS = True

ZONE_LABEL = ZONE_MSOA and not ZONE_MSOA_PWC
RAIL_NETWORK = TRANSPORT
MAJOR_ROAD_NETWORK = TRANSPORT
STRATEGIC_ROAD_NETWORK = TRANSPORT
MOTORWAY_JUNCTION = TRANSPORT

# Additional metadata for each layer
WATER_COLOUR = "#9BD6EB"
RAIL_COLOUR = "#000000"
ALL_MSOA_COLOUR = "#d1c7b4"
ZONE_MSOA_COLOUR = "#dd7824"
MSOA_OUTLINE = "#413c35"
MAJOR_ROAD_COLOUR = "#e01818"
STRATEGIC_ROAD_COLOUR = "#2518e0"
PWC_COLOUR = "#e0c618"
EXCLUDE_COLOUR = "#FF0000"
JOURNEY_COLOUR = "#F5349E"

LINE_SIZE = 0.7
POINT_SIZE = 4

ROADS = {'M5': (-3.51565, 50.68052, -2.60899, 51.52884), 'A38': (-3.257, 50.95, -2.591, 51.5), 'A361': (-4.0, 50.0, -2.8, 51.2), 'A370': (-3.0, 51.3, -2.591, 51.5)}
DELTA = 0.0001
ZONE_NAMES = {"bridgwater": "Bridgwater", "bristol": "Bristol", "cullompton": "Cullompton", "exeter": "Exeter", "highbridge_and_burnham": "Highbridge and Burnham-on-Sea", "taunton": "Taunton", "tiverton": "Tiverton", "wellington": "Wellington", "weston-super-mare": "Weston-super-Mare"}

bbox = {}
for road, bounds in ROADS.items():
    bbox[road] = shapely.geometry.box(bounds[0] - DELTA, bounds[1] - DELTA, bounds[2] + DELTA, bounds[3] + DELTA)

# Initialise figure and axes

fig, ax = plt.subplots(dpi=1000) # Render/save figure with high resolution
ax.axis('off') # Disable axis rendering - only view the plot

# Add background colour
ax.add_artist(ax.patch)
ax.patch.set_zorder(-1)
ax.patch.set_facecolor(WATER_COLOUR)

# Set axis limits
ax.set_xlim(-3.6422519130400954, -2.4571299138023925)
ax.set_ylim(50.63182874201171, 51.58789000812319)

# Initialise data for use later
msoa_codes: list[str] = []
zone_data: dict[str, gpd.GeoDataFrame] = {}

# Read all shapefiles and process data

# Read MSOA boundaries shapefile
if ALL_MSOA_BOUNDARIES:
    all_msoa = gpd.read_file("GIS/shapes/MSOA_Dec_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V3_2022_-6859460489122695720/MSOA_2011_EW_BSC_V3.shp")
    if all_msoa.crs is None or all_msoa.crs.to_epsg() != 4326:
        all_msoa = all_msoa.to_crs(epsg=4326)

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

# Get rail network shapefile
if RAIL_NETWORK:
    # Data from https://datashare.ed.ac.uk/handle/10283/2423

    rail = gpd.read_file("GIS/shapes/Bristol_Exeter_Railways/Bristol_Exeter_Railway.shp")
    if rail.crs is None or rail.crs.to_epsg() != 4326:
        rail = rail.set_crs(epsg=27700)
        rail = rail.to_crs(epsg=4326)

    stations = gpd.read_file("GIS/shapes/Bristol_Exeter_Railways/Bristol_Exeter_Railway_Stations.shp")
    if stations.crs is None or stations.crs.to_epsg() != 4326:
        stations = stations.set_crs(epsg=27700)
        stations = stations.to_crs(epsg=4326)

# Get major road network shapefile
if MAJOR_ROAD_NETWORK:
    # Data from https://www.data.gov.uk/dataset/95f58bfa-13d6-4657-9d6f-020589498cfd/major-road-network
    major_roads = gpd.read_file("GIS/shapes/Major_Road_Network_2018_Open_Roads/Major_Road_Network_2018_Open_Roads.shp")
    if major_roads.crs is None or major_roads.crs.to_epsg() != 4326:
        major_roads = major_roads.to_crs(epsg=4326)

    major_roads = major_roads[major_roads['roadClas_1'].isin(ROADS)]
    major_roads = major_roads[major_roads.apply(lambda row: row.geometry.within(bbox[row['roadClas_1']]), axis=1)]

# Get strategic road network shapefile
if STRATEGIC_ROAD_NETWORK:
    # Data from https://data-tfwm.opendata.arcgis.com/datasets/tfwm::strategic-road-network/about

    strategic_roads = gpd.read_file("GIS/shapes/Strategic_Road_Network/Strategic_Road_Network.shp")
    if strategic_roads.crs is None or strategic_roads.crs.to_epsg() != 4326:
        strategic_roads = strategic_roads.to_crs(epsg=4326)

    strategic_roads = strategic_roads[strategic_roads['roadname'].isin(ROADS)]

    strategic_roads = strategic_roads[strategic_roads.apply(lambda row: row.geometry.within(bbox[row['roadname']]), axis=1)]

# Get motorway junctions shapefiles
if MOTORWAY_JUNCTION:
    # Data from https://osdatahub.os.uk/data/downloads/open/OpenRoads

    junctions_st = gpd.read_file("GIS/shapes/Motorway_Junctions/ST_MotorwayJunction.shp")
    if junctions_st.crs is None or junctions_st.crs.to_epsg() != 4326:
        junctions_st = junctions_st.to_crs(epsg=4326)

    junctions_sx = gpd.read_file("GIS/shapes/Motorway_Junctions/SX_MotorwayJunction.shp")
    if junctions_sx.crs is None or junctions_sx.crs.to_epsg() != 4326:
        junctions_sx = junctions_sx.to_crs(epsg=4326)

    junctions = gpd.GeoDataFrame(pd.concat([junctions_st, junctions_sx], ignore_index=True))

    junctions = junctions[junctions['number'].str[0:2].isin(ROADS)]

    junctions = junctions[junctions.intersects(bbox['M5'])]

# Get Population-Weighted Centroid (PWC) for each MSOA in our zones
pwc = gpd.read_file("GIS/shapes/MSOA_Dec_2011_PWC_in_England_and_Wales_2022_-4970423835205684272/MSOA_Dec_2011_PWC_in_England_and_Wales.shp")
pwc = pwc[pwc['msoa11cd'].isin(msoa_codes)]
if pwc.crs is None or pwc.crs.to_epsg() != 4326:
    pwc = pwc.to_crs(epsg=4326)

# Get positions of each MSOA's PWC
pwc_pos: dict[str, shapely.geometry.point.Point] = dict(zip(pwc['msoa11cd'].to_list(), pwc['geometry'].to_list()))

if JOURNEYS:
    journeys: pd.DataFrame = pd.read_csv("output/api_journeys.csv")

    lines: list[shapely.geometry.LineString] = []

    for row in journeys.itertuples():
        residence = str(row.residence)
        workplace = str(row.workplace)
        if residence in pwc_pos and workplace in pwc_pos:
            lines.append(shapely.geometry.LineString([pwc_pos[residence], pwc_pos[workplace]]))
        else:
            lines.append(shapely.geometry.LineString([]))

    gdf = gpd.GeoDataFrame(journeys, geometry=lines, crs="EPSG:4326")

    categories = gdf['mode'].astype("category")
    color_map = dict(zip(categories.cat.categories, plt.cm.tab10.colors[:len(categories.cat.categories)]))
    gdf['color'] = gdf['mode'].map(color_map)

    gdf['size'] = gdf['number'] / gdf['number'].max() * 3

    gdf.plot(ax=ax, color=gdf['color'], linewidth=gdf['size'], zorder=10)

# Plot each GeoDataFrame

# Plot MSOA boundaries
if ALL_MSOA_BOUNDARIES:
    all_msoa.plot(ax=ax, color=ALL_MSOA_COLOUR, edgecolor=MSOA_OUTLINE, linewidth=0.15, zorder=1)

# Plot each zone
if ZONE_MSOA:
    journey_data = pd.read_csv('output/api_journeys.csv') # Data about different journeys, using Google Maps API and WU03EW table
    area_data = pd.read_csv('data/SAM_MSOA_DEC_2011_EW.csv') # Area of each MSOA, data from https://geoportal.statistics.gov.uk/datasets/standard-area-measurements-for-census-areas-including-oas-lsoas-msoas-december-2011-in-ew/about

    modes = ['train'] # Modes of transport to visualise

    residence_number: dict[str, tuple] = {}
    workplace_number: dict[str, tuple] = {}
    residence_workplace_number: dict[str, tuple] = {}

    areas: dict[str, float] = {}

    for row in journey_data.itertuples():
        if len(modes) == 0 or str(row.mode) in modes:
            residence = str(row.residence)
            workplace = str(row.workplace)
            number = (int(str(row.number)), int(str(row.number)) * int(str(row.distance)), int(str(row.number)) * int(str(row.time)))
            if residence == workplace:
                if residence in residence_workplace_number:
                    residence_workplace_number[residence] = tuple(x + y for x, y in zip(residence_workplace_number[residence], number))
                else:
                    residence_workplace_number[residence] = number
            else:
                if residence in residence_number:
                    residence_number[residence] = tuple(x + y for x, y in zip(residence_number[residence], number))
                else:
                    residence_number[residence] = number
                    
                if workplace in workplace_number:
                    workplace_number[workplace] = tuple(x + y for x, y in zip(workplace_number[workplace], number))
                else:
                    workplace_number[workplace] = number

    for row in area_data.itertuples():
        areas[str(row.MSOA11CD)] = float(str(row.AREALHECT))

    vmin = None
    vmax = None

    zone_min = []
    zone_max = []

    cmap: colors.Colormap
    norm: colors.Normalize

    values = {}

    if ZONE_COLOURS:
        for name, zone in zone_data.items():
            numbers = []
            for row in zone.itertuples():
                msoa_code = str(row.MSOA11CD)
                num_journeys = (
                    (residence_number[msoa_code][0] if msoa_code in residence_number else 0) + 
                    (workplace_number[msoa_code][0] if msoa_code in workplace_number else 0) + 
                    (residence_workplace_number[msoa_code][0] if msoa_code in residence_workplace_number else 0))
                
                avg_distance = float('inf') if num_journeys == 0 else (
                    (residence_number[msoa_code][1] if msoa_code in residence_number else 0) + 
                    (workplace_number[msoa_code][1] if msoa_code in workplace_number else 0) + 
                    (residence_workplace_number[msoa_code][1] if msoa_code in residence_workplace_number else 0)) / num_journeys
                
                avg_time = float('inf') if num_journeys == 0 else (
                    (residence_number[msoa_code][2] if msoa_code in residence_number else 0) + 
                    (workplace_number[msoa_code][2] if msoa_code in workplace_number else 0) + 
                    (residence_workplace_number[msoa_code][2] if msoa_code in residence_workplace_number else 0)) / num_journeys

                numbers.append(num_journeys)

            filtered_numbers = [x for x in numbers if x < float('inf')]
            if len(filtered_numbers) > 0:
                zone_min.append(min(filtered_numbers))
                zone_max.append(max(filtered_numbers))
            
            values[name] = numbers

        if len(zone_min) > 0:
            vmin = min(zone_min)
            vmax = max(zone_max)

        cmap = plt.get_cmap('viridis').copy()
        cmap.set_under(EXCLUDE_COLOUR)
        cmap.set_over(EXCLUDE_COLOUR)
        norm = colors.Normalize(vmin=vmin, vmax=vmax)

        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        cmap_padding = 0.05
        cmap_width = 0.015
        cmap_height = 0.15
        aspect = (ylim[1] - ylim[0]) / (xlim[1] - xlim[0])
        cmap_vertical_padding = cmap_padding * aspect

        pcm = ax.pcolormesh(np.random.randn(20, 20), cmap='viridis', vmin=vmin, vmax=vmax)
        cax = ax.inset_axes((cmap_padding, 1.0 - cmap_vertical_padding - cmap_height, cmap_width, cmap_height))
        cbar = fig.colorbar(pcm, cax=cax, orientation='vertical')
        cbar.ax.tick_params(labelsize=3)

    for name, zone in zone_data.items():
        if ZONE_COLOURS:
            numbers = [(x if math.isfinite(x) else vmax + 1.0) for x in values[name]]
            zone['numbers'] = numbers
            zone.plot(ax=ax, column='numbers', cmap=cmap, norm=norm, edgecolor=MSOA_OUTLINE, linewidth=0.15, zorder=2)
        else:
            zone.plot(ax=ax, color=ZONE_MSOA_COLOUR, edgecolor=MSOA_OUTLINE, linewidth=0.15, zorder=2)

# Plot rail network
if RAIL_NETWORK:
    rail.plot(ax=ax, color=RAIL_COLOUR, linewidth=LINE_SIZE, zorder=3)

# Plot major road network
if MAJOR_ROAD_NETWORK:
    major_roads.plot(ax=ax, color=MAJOR_ROAD_COLOUR, linewidth=LINE_SIZE, zorder=4)

# Plot strategic road network
if STRATEGIC_ROAD_NETWORK:
    strategic_roads.plot(ax=ax, color=STRATEGIC_ROAD_COLOUR, linewidth=LINE_SIZE, zorder=5)

# Plot Population-Weighted Centroid (PWC) for each MSOA in our zones
if ZONE_MSOA_PWC:
    pwc.plot(ax=ax, color=PWC_COLOUR, edgecolor='black', markersize=POINT_SIZE, linewidth=0.1 * POINT_SIZE, zorder=6)

# Plot railway stations
if RAIL_NETWORK:
    stations.plot(ax=ax, color='white', edgecolor=RAIL_COLOUR, markersize=POINT_SIZE, linewidth=LINE_SIZE, zorder=7)

# Plot motorway junctions
if MOTORWAY_JUNCTION:
    junctions.plot(ax=ax, color='white', edgecolor=STRATEGIC_ROAD_COLOUR, markersize=POINT_SIZE, linewidth=LINE_SIZE, zorder=8)

if ZONE_LABEL:
    for name, zone in zone_data.items():
        centroids = zone.geometry.centroid
        x, y = np.mean(np.column_stack((centroids.x.to_list(), centroids.y.to_list())), axis=0)
        ax.text(x, y, ZONE_NAMES[name], fontsize=4, ha='center', va='bottom', bbox=dict(
            facecolor="white",  # box background color
            edgecolor="black",        # box border color
            boxstyle="round,pad=0.3",  # rounded corners with padding
            linewidth=0.6
        ),
        zorder=9)

if TRANSPORT and not ZONE_COLOURS:
    strategic_road_line = Line2D([0], [0], linewidth=LINE_SIZE, color=STRATEGIC_ROAD_COLOUR, label='M5')
    major_road_line = Line2D([0], [0], linewidth=LINE_SIZE, color=MAJOR_ROAD_COLOUR, label='Major Roads')
    rail_line = Line2D([0], [0], linewidth=LINE_SIZE, color=RAIL_COLOUR, label='Railways')
    junction_point = Line2D([0], [0], color=STRATEGIC_ROAD_COLOUR, marker='o', linestyle='', markerfacecolor='white', markersize=POINT_SIZE, linewidth=LINE_SIZE, label='Motorway Junctions')
    station_point = Line2D([0], [0], color=RAIL_COLOUR, marker='o', linestyle='', markerfacecolor='white', markersize=POINT_SIZE, linewidth=LINE_SIZE, label='Railway Stations')
    plt.legend(fontsize='xx-small', handles=[strategic_road_line, major_road_line, rail_line, junction_point, station_point])
        
# Remove any padding for cleaner image
plt.tight_layout()
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Save generated map
filename = f"graphs/{PLOT_NAME}.png"
plt.savefig(filename, bbox_inches='tight', pad_inches=0)