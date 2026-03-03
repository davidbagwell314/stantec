import shapefile
import pandas as pd
import duckdb
import csv
import os
import sys

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
    csv_src = 'data/wu03ew_v2.csv'

    con = duckdb.connect()

    # Get column names
    header = ["residence","workplace","all","home","metro","train","bus","taxi","motorcycle","driving","passenger","bicycle","foot","other"]

    # All columns are VARCHAR type
    schema = {col: "VARCHAR" for col in header}

    # Fetch all required data
    return con.execute(
        f"""SELECT * 
            FROM read_csv_auto('{csv_src}', columns={schema})
            WHERE residence = '{residence}'
        """
    ).fetchdf()

def fetch_MSOA_PWC(codes):
    csv_src = 'data/MSOA_Dec_2011_PWC_in_England_and_Wales_2022_-7657754233007660732.csv'

    con = duckdb.connect()
        
    # Get column names
    with open(csv_src, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)

    # All columns are VARCHAR type
    schema = {col: "VARCHAR" for col in header}

    df = pd.DataFrame({'code': codes})
    con.register("codes", df)

    # Fetch all required data
    return con.execute(
        f"""SELECT * 
            FROM read_csv_auto('{csv_src}', columns={schema})
            WHERE MSOA11CD IN (SELECT code FROM codes)
        """
    ).fetchdf()

if __name__ == "__main__":
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

    # Display all rows of the dataframe
    pd.set_option('display.max_rows', None)

    for name, file in zone_files.items():
        print(f"{name}:")
        df = get_shapefile_records(file)
        if df is None:
            print(f"No records found for {name}")
        else:
            zones.update({name: df})
            print(df.to_string(index=False))
            print()

    journeys: dict[tuple[str, str], tuple] = {}
    distances: dict[tuple[str, str], float] = {}

    for row in zones["taunton"].itertuples(index=False):
        # Location of residence, location of workplace, number of people by method of travel
        wu03ew_table = fetch_wu03ew(row.MSOA11CD)
        print(wu03ew_table.head())
        print()

        # List of all workplace locations for this location of residence
        workplace_list = []

        # "residence","workplace","all","home","metro","train","bus","taxi","motorcycle","driving","passenger","bicycle","foot","other"
        for wu03ew_row in wu03ew_table.itertuples(index=False):
            data = tuple([int(str(x)) for i, x in enumerate(wu03ew_row) if i > 1])
            if data[0] > 5:
                journeys[(str(wu03ew_row.residence), str(wu03ew_row.workplace))] = data
                workplace_list.append(str(wu03ew_row.workplace))

        print(workplace_list)
        print(journeys)
        print(len(journeys))

        # Population-weighted centroid for location of residence
        residence_pwc = fetch_MSOA_PWC([row.MSOA11CD])
        print(residence_pwc.head())
        print()

        # Population-weighted centroid for location of workplace
        workplace_pwc = fetch_MSOA_PWC(workplace_list)
        print(workplace_pwc.head())
        print()

        x1, y1 = float(residence_pwc.iloc[0].x), float(residence_pwc.iloc[0].y)
        for pwc in workplace_pwc.iloc:
            x2, y2 = float(pwc.x), float(pwc.y)
            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            #print(f"{pwc.MSOA11CD}: {dist}")
            distances[(str(residence_pwc.iloc[0].MSOA11CD), str(pwc.MSOA11CD))] = dist

        break

    print(distances)