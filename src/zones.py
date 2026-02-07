import shapefile
import pandas as pd
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