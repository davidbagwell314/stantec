# Ignore for now
# Script to get DfT traffic counts for a road in our region

import duckdb
import csv
import pandas as pd

road = 'all' # replace with other roads (i.e. 'A38')

csv_src = 'data/dft_traffic_counts_raw_counts.csv'
csv_dest = f'data/{road.lower()}_traffic.csv'

con = duckdb.connect()

# Get column names
with open(csv_src, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)

# All columns are VARCHAR type
schema = {col: "VARCHAR" for col in header}

# Data returned will be from our road (either M5 or A38), region (region 1, AKA South West), and year (since 2022)
# Copy all required data to new csv file
con.execute(
    f"""COPY (SELECT * 
        FROM read_csv_auto('{csv_src}', columns={schema})
        WHERE local_authority_id IN ('115', '70', '183', '5', '143', '71', '144') AND year >= '2022')
        TO '{csv_dest}'
        WITH (HEADER, DELIMITER ',')
    """
)