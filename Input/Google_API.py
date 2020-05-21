import requests
import os
import json


def write_driving_times(stations):

    driving_times = {}

    for st1 in stations:
        for st2 in stations:
            if st2.id not in st1.station_car_travel_time.keys():
                t = get_driving_time(st1.latitude, st1.longitude, st2.latitude, st2.longitude)
                print(t)
                st1.station_car_travel_time[st2.id] = t[0]
        driving_times[st1.id] = st1.station_car_travel_time
    with open('../Input/times.json', 'w') as fp:
        json.dump(driving_times, fp)


def get_driving_time(origin_lat, origin_lon, dest_lat, dest_lon):
    base = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial"
    key = os.environ['KEY2']

    parameters = {'origins': "{},{}".format(origin_lat, origin_lon), 'destinations': "{},{}".format(dest_lat, dest_lon),
                  'key': key}
    r = requests.get(base, params=parameters)
    data = r.json()
    print(data)
    origin_address = data['origin_addresses'][0].split(',')[0]
    destination_address = data['destination_addresses'][0].split(',')[0]
    return [round(int(data['rows'][0]['elements'][0]['duration']['value']) / 60, 2), origin_address,
            destination_address]