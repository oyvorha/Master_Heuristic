import json
from Station import Station


def get_driving_time_from_id(station_id_1, station_id_2):
    id_key = str(station_id_1) + '_' + station_id_2
    with open('Input/times.json', 'r') as f:
        time_json = json.load(f)
    return time_json[id_key]


def generate_all_stations(scenario):
    with open('Input/station.json', 'r') as f:
        stations = json.load(f)

    station_objects = []
    for id, station in stations.items():
        latitude = float(station[0])
        longitude = float(station[1])
        init_battery_load = station[2][scenario][0]
        init_flat_load = station[2][scenario][1]
        incoming_charged_bike_rate = station[2][scenario][2]
        incoming_flat_bike_rate = station[2][scenario][3]
        outgoing_charged_bike_rate = station[2][scenario][4]
        ideal_state = 10
        obj = Station(latitude, longitude, init_battery_load, init_flat_load
                      , incoming_charged_bike_rate, incoming_flat_bike_rate, outgoing_charged_bike_rate, ideal_state,
                      id)
        station_objects.append(obj)
    return station_objects
