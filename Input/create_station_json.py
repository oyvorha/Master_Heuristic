import pandas as pd
import json

file = '~/Documents/optimal_state.xlsx'
sheet_name = 'Ark 1'


def read_excel_and_set_rates():
    df_stations = pd.read_excel(file, sheet_name)
    optimal_states = {}
    for index, row in df_stations.iterrows():
        if row['station_id'] in optimal_states.keys():
            optimal_states[row['station_id']][int(row['hour_utc'])] = row['optimal_state']
        else:
            optimal_states[row['station_id']] = {int(row['hour_utc']): row['optimal_state']}
    write_json(optimal_states)


def write_json(json_element):
    with open('station.json', 'w') as fp:
        json.dump(json_element, fp)


read_excel_and_set_rates()
