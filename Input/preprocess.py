import json


def get_driving_time_from_id(station_id_1, station_id_2):
    id_key = str(station_id_1) + '_' + station_id_2
    with open("times.json", 'r') as f:
        time_json = json.load(f)
    return time_json[id_key]