import os

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