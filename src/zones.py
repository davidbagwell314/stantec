import shapefile
import pandas as pd
import duckdb
import csv
import os
import sys
import convert

connected_wu03ew = False
con_wu03ew: duckdb.DuckDBPyConnection
header_wu03ew: list[str]
schema_wu03ew: dict[str, str]
connected_MSOA = False
con_MSOA: duckdb.DuckDBPyConnection
reader_MSOA = 0
header_MSOA: list[str]
schema_MSOA: dict[str, str]

def error(msg: str = "") -> None:
    print(msg)
    exit()

def get_shapefile_records(shapefile_path: (str | os.PathLike[str])) -> (pd.DataFrame | None):
    try:
        # Check shapefile exists
        if not os.path.exists(shapefile_path):
            raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

        # Read shapefile
        sf = shapefile.Reader(shapefile_path)

        # Extract field names (excluding the first deletion flag field)
        fields = [field[0] for field in sf.fields[1:]]

        # Extract records (attribute data)
        records = [list(record) for record in sf.records()]

        # Create a DataFrame with fields and records
        df = pd.DataFrame(records, columns=fields)
  
        return df

    except shapefile.ShapefileException as e:
        error(f"Error reading shapefile: {e}")
    except Exception as e:
        error(f"Unexpected error: {e}")

    return None

def view_shapefile_fields(shapefile_path):
    try:
        # Check shapefile exists
        if not os.path.exists(shapefile_path):
            raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

        # Read shapefile
        sf = shapefile.Reader(shapefile_path)

        fields = [field[0] for field in sf.fields[1:]]
        print("Fields:", fields)

        # Get records
        records = sf.records()
        print(f"\nTotal records: {len(records)}\n")

        # Display records
        for i, record in enumerate(records):
            print(f"Record {i+1}:")
            for field_name, value in zip(fields, record):
                print(f"  {field_name}: {value}")
            print("-" * 40)

    except shapefile.ShapefileException as e:
        print(f"Error reading shapefile: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def fetch_wu03ew(residence):
    global connected_wu03ew, con_wu03ew, header_wu03ew, schema_wu03ew
    csv_src = 'data/wu03ew_v2.csv'

    if not connected_wu03ew:
        connected_wu03ew = True
        con_wu03ew = duckdb.connect()

        # Get column names
        header_wu03ew = ["residence","workplace","all","home","metro","train","bus","taxi","motorcycle","driving","passenger","bicycle","foot","other"]

        # All columns are VARCHAR type
        schema_wu03ew = {col: "VARCHAR" for col in header_wu03ew}

    # Fetch all required data
    return con_wu03ew.execute(
        f"""SELECT * 
            FROM read_csv_auto('{csv_src}', columns={schema_wu03ew})
            WHERE residence = '{residence}'
        """
    ).fetchdf()

def fetch_MSOA_PWC(codes):
    global connected_MSOA, con_MSOA, reader_MSOA, header_MSOA, schema_MSOA
    csv_src = 'data/MSOA_Dec_2011_PWC_in_England_and_Wales_2022_-7657754233007660732.csv'

    if not connected_MSOA:
        connected_MSOA = True
        con_MSOA = duckdb.connect()
            
        # Get column names
        with open(csv_src, newline='', encoding='utf-8') as f:
            reader_MSOA = csv.reader(f)
            header_MSOA = next(reader_MSOA)

        # All columns are VARCHAR type
        schema_MSOA = {col: "VARCHAR" for col in header_MSOA}

    df = pd.DataFrame({'code': codes})
    con_MSOA.register("codes", df)

    # Fetch all required data
    return con_MSOA.execute(
        f"""SELECT * 
            FROM read_csv_auto('{csv_src}', columns={schema_MSOA})
            WHERE MSOA11CD IN (SELECT code FROM codes)
        """
    ).fetchdf()

def get_zone_data(num_journeys: int) -> dict[str, tuple[dict[tuple[str, str], tuple[int, int, int, int, int, int, int, int, int, int, int, int]], dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]], dict[str, tuple[float, float]], list[str]]]:
    data_path = r"GIS\shapes"

    zone_files: dict[str, str] = {}
    zones: dict[str, pd.DataFrame] = {}

    # Find the shapefiles for each zone
    for root, dirs, files in os.walk(data_path):
        for n in files:
            name, extension = os.path.splitext(n)
            if extension == ".shp":
                fp = os.path.join(root, n)
                zone_files.update({name: fp})
        break

    # Get records for each zone
    for name, file in zone_files.items():
        df = get_shapefile_records(file)
        if df is None:
            print(f"No records found for {name}")
        else:
            zones.update({name: df})

    # Info about zone_data dictionary:
    # Key: name of zone (e.g. 'bridgwater')
    # Value: tuple of journeys, distances, and locations
    # Type: dict[str, tuple[dict[tuple[str, str], tuple[int, int, int, int, int, int, int, int, int, int, int, int]], dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]], dict[str, tuple[float, float]]]]

    # Info about journeys dictionary:
    # Key: tuple of origin and destination MSOA codes
    # Value: tuple of number of people on various modes of transport (from wu03ew table)
    # Type: dict[tuple[str, str], tuple[int, int, int, int, int, int, int, int, int, int, int, int]]

    # Info about distances dictionary:
    # Key: tuple of origin and destination MSOA codes
    # Value: tuple of latitude and longitude of both origin and destination, and straight-line distance between these (metres)
    # Type: dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]]

    # Info about locations dictionary:
    # Key: MSOA code
    # Value: tuple of latitude and longitude
    # Type: dict[str, tuple[float, float]]

    zone_data = {}

    for name, zone in zones.items():
        # key for both is the residence MSOA and the workplace MSOA
        journeys: dict[tuple[str, str], tuple] = {} # value is data from wu03ew
        distances: dict[tuple[str, str], tuple[tuple[float, float], tuple[float, float], float]] = {} # value is easting and northing for residence and workplace, as well as distance (m)

        locations: dict[str, tuple[float, float]] = {} # stores location of all MSOAs in distances
        codes: list[str] = [] # stores all MSOA codes for each zone

        for row in zone.itertuples(index=False):
            codes.append(str(row.MSOA11CD))

            # Location of residence, location of workplace, number of people by method of travel
            wu03ew_table = fetch_wu03ew(row.MSOA11CD)

            # List of all workplace locations for this location of residence
            workplace_list = []

            # Process wu03ew data
            # wu03ew columns: residence, workplace, all, home, metro, train, bus, taxi, motorcycle, driving, passenger, bicycle, foot, other
            for wu03ew_row in wu03ew_table.itertuples(index=False):
                data = tuple([int(str(x)) for i, x in enumerate(wu03ew_row) if i > 1])
                if data[0] > num_journeys:
                    journeys[(str(wu03ew_row.residence), str(wu03ew_row.workplace))] = data
                    workplace_list.append(str(wu03ew_row.workplace))

            # Population-weighted centroid for location of residence
            residence_pwc = fetch_MSOA_PWC([row.MSOA11CD])

            # Population-weighted centroid for location of workplace
            workplace_pwc = fetch_MSOA_PWC(workplace_list)

            # Get latitude and longitude for each MSOA
            x1, y1 = float(residence_pwc.iloc[0].x), float(residence_pwc.iloc[0].y)
            for pwc in workplace_pwc.iloc:
                x2, y2 = float(pwc.x), float(pwc.y)
                dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

                src = convert.convert_easting_northing_to_latlon(x1, y1)
                dest = convert.convert_easting_northing_to_latlon(x2, y2)
                
                distances[(str(residence_pwc.iloc[0].MSOA11CD), str(pwc.MSOA11CD))] = (src, dest, dist)
                locations[str(residence_pwc.iloc[0].MSOA11CD)] = src
                locations[str(pwc.MSOA11CD)] = dest

        zone_data[name] = (journeys, distances, locations, codes)

    return zone_data