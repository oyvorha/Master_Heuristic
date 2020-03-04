import pandas as pd
import json

file = '~/stations.xlsx'
sheet_name = 'Data'
scenarios = ['A', 'B', 'C', 'D', 'E']
flat_rate = 0.3
battery_rate = 0.7
length_time_interval = 120

stations = {}


def read_excel():
    df_stations = pd.read_excel(file, sheet_name)
    for index, row in df_stations.iterrows():
        interval_scenarios = {}
        for scenario in scenarios:
            init_load = round(battery_rate * float(row[scenario+'_start_load']), 3)
            init_flat_load = round(flat_rate * float(row[scenario + '_start_load']), 3)
            incoming_battery_rate = round(battery_rate * float(row[scenario + '_incoming'])/length_time_interval, 3)
            incoming_flat_rate = round(flat_rate * float(row[scenario + '_incoming'])/length_time_interval, 3)
            outgoing_rate = round(float(row[scenario + '_outgoing_rate']) / length_time_interval, 3)
            demand = calculate_demand(float(row[scenario + '_outgoing_rate']), row[scenario+'_empty'])
            interval_scenarios[scenario] = [init_load, init_flat_load, incoming_battery_rate, incoming_flat_rate,
                                            outgoing_rate, demand]
        stations[int(row['Station_ID'])] = [row['Latitude'], row['Longitude'], interval_scenarios]


def calculate_demand(trips, empty_time):
    demand_rate = trips / (length_time_interval - empty_time)
    return round(demand_rate, 2)


def write_json(json_element):
    with open('station.json', 'w') as fp:
        json.dump(json_element, fp)


read_excel()
write_json(stations)