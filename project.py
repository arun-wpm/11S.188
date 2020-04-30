import pandas
import requests
import json
import numpy as np
from datetime import datetime
from geopy import distance

API_KEY = "134a8e9b40194b06b729f9481beee3f4"

# Get census block information
df = pandas.read_csv("E:/My Schoolwork/Y1.2 Frosh Spring/11.S188/project/massachusetts-census-block-groups-2010.csv")
print(df.columns)
df = df.fillna(0)
df = df.sort_values('POP100_RE')
# for i in range(1, 10):
#     print(df['INTPTLAT10'].values[-i], df['INTPTLON10'].values[-i], df['POP100_RE'].values[-i])

# Get MBTA stop information into dataStop
url = "https://api-v3.mbta.com/stops"
response = requests.get(url)
data = response.text
parsed = json.loads(data)
dataStop = {}
stopWaitTime = {}
# print(json.dumps(parsed))

# Get MBTA schedule information and distill it into stopWaitTime
print(len(parsed["data"]))
for j in range(len(parsed["data"])):
# for j in range(10):
    stopId = parsed["data"][j]["id"]
    if not stopId.isnumeric():
        continue
    # print(parsed["data"][i]["id"],
    #       parsed["data"][i]["attributes"]["vehicle_type"],
    #       parsed["data"][i]["attributes"]["latitude"],
    #       parsed["data"][i]["attributes"]["longitude"],
    #       parsed["data"][i]["attributes"]["name"])
    urlStop = "https://api-v3.mbta.com/schedules?filter[stop]="+stopId+"&api_key="+API_KEY
    response = requests.get(urlStop)
    dataStop[stopId] = json.loads(response.text)
    schedule = []
    for node in dataStop[stopId]["data"]:
        # print(node["attributes"]["departure_time"])
        if node["attributes"]["departure_time"] is None:
            continue
        schedule.append(datetime.strptime(node["attributes"]["departure_time"], "%Y-%m-%dT%H:%M:%S-05:00"))
    schedule.sort()
    if len(schedule) < 5: # only those which have at least 5 departures
        continue
    sum = 0
    for i in range(1, len(schedule)):
        # print(schedule[i] - schedule[i - 1])
        sum += (schedule[i] - schedule[i - 1]).total_seconds()
    sum /= len(schedule)
    stopWaitTime[stopId] = [sum, parsed["data"][i]["attributes"]["latitude"], parsed["data"][i]["attributes"]["longitude"], len(schedule)]
    # print(stopId, sum)
    if j%100 == 0:
        print(j)
dataStopdf = pandas.DataFrame.from_dict(dataStop, orient="index")
# print(dataStopdf)
dataStopdf.to_csv("E:/My Schoolwork/Y1.2 Frosh Spring/11.S188/project/dataStop.csv", encoding='utf-8', index=False)
swt = np.asarray([[k, stopWaitTime[k][0], stopWaitTime[k][1], stopWaitTime[k][2]] for k in stopWaitTime])
print(swt)
np.savetxt("E:/My Schoolwork/Y1.2 Frosh Spring/11.S188/project/stopWaitTime.csv", swt, fmt="%5s", delimiter=",")

# Calculating the most optimal stop from a census block
df["metricValue"] = np.zeros(len(df.index))
df["metricDist"] = np.zeros(len(df.index))
df["metricWait"] = np.zeros(len(df.index))
for i in range(len(df.index)):
    bestVal = None
    bestValTuple = None
    for j in range(len(parsed["data"])):
    # for j in range(10):
        stopId = parsed["data"][j]["id"]
        if not stopId.isnumeric():
            continue
        if stopId not in stopWaitTime:
            continue
        dist = distance.distance((df['INTPTLAT10'].values[i], df['INTPTLON10'].values[i]),
                                     (parsed["data"][j]["attributes"]["latitude"], parsed["data"][j]["attributes"]["longitude"])).kilometers
        # print(dist, stopWaitTime[parsed["data"][j]["id"]])
        if bestVal is None:
            bestVal = dist*stopWaitTime[stopId][0]/60
            bestValTuple = (dist, stopWaitTime[stopId][0]/60)
        else:
            bestVal = min(bestVal, dist*stopWaitTime[stopId][0]/60)
            if bestVal == dist*stopWaitTime[stopId][0]/60:
                bestValTuple = (dist, stopWaitTime[stopId][0]/60)
        # print(bestVal)
    df["metricValue"].values[i] = bestVal
    df["metricDist"].values[i] = bestValTuple[0]
    df["metricWait"].values[i] = bestValTuple[1]

df.to_csv("E:/My Schoolwork/Y1.2 Frosh Spring/11.S188/project/calculatedData.csv", encoding='utf-8', index=False)
