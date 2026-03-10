# Script to convert eastings and northings to latitude and longitude

from pyproj import Transformer
import csv

DATASET_PATH = r"PATH_TO_MSOA_LOCATIONS_CSV"

cache: dict[tuple[float, float], tuple[float, float]] = {}

def extract_csv(path):
    file = open(path, "r")
    reader = csv.reader(file)
    dataList = list(reader)
    dataList.pop(0)
    return dataList

def convert_easting_northing_to_latlon(easting, northing):
    global cache
    """
    Convert British National Grid (OSGB36) Easting/Northing to WGS84 Latitude/Longitude.

    Parameters:
        easting (float): Easting in meters
        northing (float): Northing in meters

    Returns:
        (lat, lon) tuple in decimal degrees
    """
    if (easting, northing) in cache:
        return cache[(easting, northing)]
    else:
        try:
            # Transformer from EPSG:27700 (OSGB36) to EPSG:4326 (WGS84)
            transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(easting, northing)
            cache[(easting, northing)] = (lat, lon)
            return lat, lon
        except Exception as e:
            raise ValueError(f"Conversion failed: {e}")

if __name__ == "__main__":
    dataset = extract_csv(DATASET_PATH)
    coords = []
    for i in range(len(dataset)):
        coord = tuple(dataset[i][4:])
        coords.append(coord)
    for easting, northing in coords:
        lat, lon = convert_easting_northing_to_latlon(easting, northing)
        print(f"{lat:.8f}, {lon:.8f}")