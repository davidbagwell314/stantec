# Stantec EMC Project

## Requirements

`GIS/zones.qgz` requires QGIS if you want to view the QGIS project. Shapefiles (in `GIS/shapes`) can be viewed with other software.


`src/zones.py` requires the shapefile module - use `pip install pyshp`.

## Large files

When downloading the following, add the files to `data/`. This may involve extracting the files from a `.zip` file.

Download `wu03ew_v2.csv` from https://statistics.ukdataservice.ac.uk/dataset/wu03ew-2011-msoamsoa-location-usual-residence-and-place-work-method-travel-work.


Download `dft_traffic_counts_raw_counts.csv` from https://roadtraffic.dft.gov.uk/downloads.

## Repository structure

`data/` contains datasets used for analysis. \
`files/` contains files unrelated to the code and data, such as PowerPoints. \
`GIS/` contains the GIS project used to represent data visually. \
`graphs/` contains graphs used to represent data visually. \
`output/` contains files and data produced by our analysis. \
`src/` contains the code.

## Google Maps API

`output/journeys/` contains JSON data for requests for Compute Route Matrix. Filenames specify the zone of residence, the group of origins and destinations used, and the method of transport used. \

`output/responses/` contains JSON data for responses from Compute Route Matrix. Filenames specify the zone of residence, the group of origins and destinations used, and the method of transport used. \

`output/api_journeys_idx.csv` contains the MSOA codes and their index used by Compute Route Matrix, for both locations of residence and workplace. When getting the response from Compute Route Matrix, use this to map the `originIndex` and `destinationIndex` to their respective MSOA codes. Columns are: `zone`, `mode`, `residence`, `workplace`, `originIndex`, `destinationIndex`. \

`output/api_journeys.csv` contains journey times and distances for different modes of transport, and the number of people for each journey, based on the outputs from `output/responses/` and the `wu03ew` table. Columns are: `zone_residence`, `zone_workplace`, `mode`, `residence`, `workplace`, `number`, `distance`, `time`