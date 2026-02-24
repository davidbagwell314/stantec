from pyproj import Transformer

def convert_easting_northing_to_latlon(easting, northing):
    """
    Convert British National Grid (OSGB36) Easting/Northing to WGS84 Latitude/Longitude.

    Parameters:
        easting (float): Easting in meters
        northing (float): Northing in meters

    Returns:
        (lat, lon) tuple in decimal degrees
    """
    try:
        # Transformer from EPSG:27700 (OSGB36) to EPSG:4326 (WGS84)
        transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(easting, northing)
        return lat, lon
    except Exception as e:
        raise ValueError(f"Conversion failed: {e}")

if __name__ == "__main__":
    for easting, northing in [(321073.132, 123303.778000001), (291712.971,90432.4069999997)]:
        lat, lon = convert_easting_northing_to_latlon(easting, northing)
        print(f"{lat:.8f}, {lon:.8f}")