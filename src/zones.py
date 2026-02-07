import shapefile
import os
import sys

def get_shapefile_records(shapefile_path):
    try:
        # Check shapefile exists
        if not os.path.exists(shapefile_path):
            raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

        # Read shapefile
        sf = shapefile.Reader(shapefile_path)

        fields = [field[0] for field in sf.fields[1:]]
        records = []
        records_raw = sf.records()

        for record in records_raw:
            records.append(dict(zip(fields, record)))
  
        return records

    except shapefile.ShapefileException as e:
        print(f"Error reading shapefile: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

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

    for root, dirs, files in os.walk(data_path):
        for n in files:
            name, extension = os.path.splitext(n)
            if extension == ".shp":
                fp = os.path.join(root, n)
                zone_files.update({name: fp})
        break

    print(zone_files)

    for name, file in zone_files.items():
        print(f"{name}:")
        records = get_shapefile_records(file)
        print(records)
        #view_fields(file)