import pandas as pd
from openpyxl import load_workbook

book = load_workbook("../Output/output.xlsx")
writer = pd.ExcelWriter("../Output/output.xlsx", engine='openpyxl')
writer.book = book

df_keys = []


def save_time_output(no_stations, branching, scenarios, no_vehicles, time):

    df = pd.DataFrame(columns=['Stations', 'Vehicles', 'Branching', 'Scenarios', 'Time'])

    new_row = {'Stations': no_stations, 'Vehicles': no_vehicles, 'Branching': branching, 'Scenarios': scenarios,
               'Time': time}

    time_df = df.append(new_row, ignore_index=True)

    if 'solution_time' in df_keys:
        start_row = writer.sheets['solution_time'].max_row
        time_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='solution_time')
        writer.save()
    else:
        time_df.to_excel(writer, index=False, sheet_name='solution_time')
        writer.save()
        df_keys.append('solution_time')
