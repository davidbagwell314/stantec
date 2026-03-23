import requests
import os
import json
import time
from secret import ROUTES_API_KEY as key

# just to prevent us from accidentally sending more requests
if True:
    print("Set boolean to False in \"src\\request.py\", line 8")
    exit()
else:
    journeysPath = "output/journeys/"
    responsesPath = "output/responses/"

    fileList = os.listdir(journeysPath)
    for i in range(len(fileList)):
        if not os.path.isfile(responsesPath + fileList[i]):
            with open(journeysPath + fileList[i], "r") as readFileObject:
                fileContents = readFileObject.read()

            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': key,
                'X-Goog-FieldMask': 'originIndex,destinationIndex,duration,distanceMeters',
            }

            response = requests.post('https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix', headers=headers, data=fileContents)
            data = response.json()

            with open(responsesPath + fileList[i], "w") as writeFileObject:
                json.dump(data, writeFileObject, indent=4)
            
            time.sleep(10)