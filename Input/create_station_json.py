import pandas as pd
import json

file = '~/stations.xlsx'
sheet_name = 'Data'
scenarios = ['A', 'B', 'C', 'D', 'E']
flat_rate = 0.3
battery_rate = 0.7
length_time_interval = 120

stations = {}


def read_excel_and_set_rates():
    df_stations = pd.read_excel(file, sheet_name)
    for index, row in df_stations.iterrows():
        interval_scenarios = {}
        for scenario in scenarios:
            full_station_time = 0  # Temporary guess: Read from DB!!
            init_load = round(float(row[scenario+'_start_load']), 0)
            docker_rate = round(float(row[scenario + '_incoming'])/(
                    length_time_interval - full_station_time), 3)
            battery_user_rate = round(float(row[scenario + '_outgoing_rate']) / (
                    length_time_interval - row[scenario+'_empty']), 3)
            interval_scenarios[scenario] = [init_load, docker_rate, battery_user_rate]
        stations[int(row['Station_ID'])] = [row['Latitude'], row['Longitude'], interval_scenarios]


def write_json(json_element):
    with open('station.json', 'w') as fp:
        json.dump(json_element, fp)


read_excel_and_set_rates()
write_json(stations)
