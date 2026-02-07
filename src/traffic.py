import duckdb
import csv
import pandas as pd

road = 'M5' # replace with other roads (i.e. 'A38')

csv_src = 'data/dft_traffic_counts_raw_counts.csv'
csv_dest = f'data/{road.lower()}_traffic.csv'

con = duckdb.connect()

# Get column names
with open(csv_src, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)

# All columns are VARCHAR type
schema = {col: "VARCHAR" for col in header}

# Copy all required data to new csv file
con.execute(
    f"""COPY (SELECT * 
        FROM read_csv_auto('{csv_src}', columns={schema})
        WHERE road_name = '{road}' AND region_id = '1' AND year >= '2022')
        TO '{csv_dest}'
        WITH (HEADER, DELIMITER ',')
    """
)