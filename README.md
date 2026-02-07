# Requirements

GIS files (in `GIS/`) are modified with QGIS - install QGIS if you want to modify these files


`zones.py` requires the shapefile module - use `pip install pyshp`

# Large files

When downloading the following, add the files to `data/`. This may involve extracting the file from z `.zip` file.

Download `wu03ew_v2.csv` from https://statistics.ukdataservice.ac.uk/dataset/wu03ew-2011-msoamsoa-location-usual-residence-and-place-work-method-travel-work


Download `dft_traffic_counts_raw_counts.csv` from https://roadtraffic.dft.gov.uk/downloads

# Repository structure

`data/` contains datasets used for analysis
`files/` contains files unrelated to the code and data, such as PowerPoints
`GIS/` contains the GIS project used to represent data visually
`src/` contains the code