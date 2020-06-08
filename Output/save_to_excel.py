import pandas as pd


def save_time_output(no_stations, branching, scenarios, no_vehicles, time, writer):
    df = pd.DataFrame(columns=['Stations', 'Vehicles', 'Branching', 'Scenarios', 'Time'])

    new_row = {'Stations': no_stations, 'Vehicles': no_vehicles, 'Branching': branching, 'Scenarios': scenarios,
               'Time': time}

    time_df = df.append(new_row, ignore_index=True)

    if 'solution_time' in writer.book.sheetnames:
        start_row = writer.sheets['solution_time'].max_row
        time_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='solution_time')
        writer.save()
    else:
        time_df.to_excel(writer, index=False, sheet_name='solution_time')
        writer.save()


def save_weight_output(set_id, scenario, env, base_s, base_c, writer):
    df = pd.DataFrame(columns=['Weight set', 'W_drive', 'W_dev', 'W_viol', 'W_net', 'Scenario', 'Total_requests',
                               'Base starvations', 'Base congestions', 'Starvations', 'Congestions'])

    new_row = {'Weight set': set_id, 'W_drive': env.crit_weights[0], 'W_dev': env.crit_weights[1], 'W_viol': env.crit_weights[2],
               'W_net': env.crit_weights[3], 'Scenario': scenario,
               'Total_requests': env.total_gen_trips, 'Base starvations': base_s, 'Base congestions': base_c,
               'Starvations': env.total_starvations, 'Congestions': env.total_congestions}

    weight_df = df.append(new_row, ignore_index=True)

    if 'Weight_simulation' in writer.book.sheetnames:
        start_row = writer.sheets['Weight_simulation'].max_row
        weight_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Weight_simulation')
        writer.save()
    else:
        weight_df.to_excel(writer, index=False, sheet_name='Weight_simulation')
        writer.save()


def save_comparison_output(scenario, sim_heur, base_s, base_c, greedy_s, greedy_c, writer, crit_off_s=None,
                           crit_off_c=None):
    df = pd.DataFrame(columns=['Scenario', 'Total_requests', 'Base starvations', 'Base congestions',
                               'Greedy starvations', 'Greedy congestions', 'Heuristic starvations',
                               'Heuristic congestions', 'Criticality off starvations', 'Criticality off congestions'])

    new_row = {'Scenario': scenario, 'Total_requests': sim_heur.total_gen_trips, 'Base starvations': base_s,
               'Base congestions': base_c, 'Greedy starvations': greedy_s, 'Greedy congestions': greedy_c,
               'Heuristic starvations': sim_heur.total_starvations, 'Heuristic congestions': sim_heur.total_congestions,
               'Criticality off starvations': crit_off_s, 'Criticality off congestions': crit_off_c}

    weight_df = df.append(new_row, ignore_index=True)

    if 'Compare_strategies' in writer.book.sheetnames:
        start_row = writer.sheets['Compare_strategies'].max_row
        weight_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Compare_strategies')
        writer.save()
    else:
        weight_df.to_excel(writer, index=False, sheet_name='Compare_strategies')
        writer.save()


def save_first_step_solution(instance, scenarios, batteries, net_charged, net_flat, next_station, writer, ideal,
                             charged, flat):

    df = pd.DataFrame(columns=['Instance', 'Scenarios', 'Next station', '#Batteries', 'Net charged load',
                               'Net flat load', 'Ideal state', 'Charged', 'Flat'])

    new_row = {'Instance': instance, 'Scenarios': scenarios, 'Next station': next_station.id, '#Batteries': batteries,
               'Net charged load': net_charged, 'Net flat load': net_flat, 'Ideal state': ideal, 'Charged': charged,
               'Flat': flat}

    weight_df = df.append(new_row, ignore_index=True)

    if 'First_solution' in writer.book.sheetnames:
        start_row = writer.sheets['First_solution'].max_row
        weight_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='First_solution')
        writer.save()
    else:
        weight_df.to_excel(writer, index=False, sheet_name='First_solution')
        writer.save()


def save_vehicle_output(day, no_veh, sim_heur, base_env, sim_greedy, writer, crit_env=None, alfa=1):
    df = pd.DataFrame(columns=['Day', 'Total_requests', 'Alfa', 'Vehicles', 'Hour', 'Base starvations', 'Base congestions',
                               'Greedy starvations', 'Greedy congestions',
                               'Heuristic starvations', 'Heuristic congestions', 'Crit-off starvations',
                               'Crit-off congestions'])

    for hour in range(len(base_env.total_starvations_per_hour)):
        new_row = {'Day': day, 'Total_requests': sim_heur.total_gen_trips, 'Alfa':alfa, 'Vehicles': no_veh, 'Hour': hour+7,
                   'Base starvations': base_env.total_starvations_per_hour[hour], 'Base congestions':
                       base_env.total_congestions_per_hour[hour],
                   'Greedy starvations': sim_greedy.total_starvations_per_hour[hour],
                   'Greedy congestions': sim_greedy.total_congestions_per_hour[hour],  'Heuristic starvations':
                       sim_heur.total_starvations_per_hour[hour], 'Heuristic congestions':
                       sim_heur.total_congestions_per_hour[hour], 'Crit-off starvations':
                       crit_env.total_starvations_per_hour[hour],  'Crit-off congestions':
                       crit_env.total_congestions_per_hour[hour]}

        weight_df = df.append(new_row, ignore_index=True)

        if 'Vehicle' in writer.book.sheetnames:
            start_row = writer.sheets['Vehicle'].max_row
            weight_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Vehicle')
            writer.save()
        else:
            weight_df.to_excel(writer, index=False, sheet_name='Vehicle')
            writer.save()

def save_vary_vehicle_output(day, no_veh, sim_heur, base_env, writer):
    df = pd.DataFrame(columns=['Day', 'Total_requests', 'Vehicles', 'Hour', 'Base starvations', 'Base congestions',
                               'Heuristic starvations', 'Heuristic congestions'])

    for hour in range(len(base_env.total_starvations_per_hour)):
        new_row = {'Day': day, 'Total_requests': sim_heur.total_gen_trips, 'Vehicles': no_veh, 'Hour': hour+7,
                   'Base starvations': base_env.total_starvations_per_hour[hour], 'Base congestions':
                       base_env.total_congestions_per_hour[hour], 'Heuristic starvations':
                       sim_heur.total_starvations_per_hour[hour], 'Heuristic congestions':
                       sim_heur.total_congestions_per_hour[hour]}

        weight_df = df.append(new_row, ignore_index=True)

        if 'Vehicle' in writer.book.sheetnames:
            start_row = writer.sheets['Vehicle'].max_row
            weight_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Vehicle')
            writer.save()
        else:
            weight_df.to_excel(writer, index=False, sheet_name='Vehicle')
            writer.save()


def save_fleet_output(day, no_rb_veh, no_bat_veh, sim_heur, base_env, writer):
    df = pd.DataFrame(columns=['Day', 'Total_requests', 'Reb_vehicles', 'Battery_vehicles', 'Hour', 'Base starvations',
                               'Base congestions', 'Heuristic starvations', 'Heuristic congestions'])

    for hour in range(len(base_env.total_starvations_per_hour)):
        new_row = {'Day': day, 'Total_requests': sim_heur.total_gen_trips, 'Reb_vehicles': no_rb_veh,
                   'Battery_vehicles': no_bat_veh, 'Hour': hour+7,
                   'Base starvations': base_env.total_starvations_per_hour[hour], 'Base congestions':
                       base_env.total_congestions_per_hour[hour], 'Heuristic starvations':
                       sim_heur.total_starvations_per_hour[hour], 'Heuristic congestions':
                       sim_heur.total_congestions_per_hour[hour]}

        weight_df = df.append(new_row, ignore_index=True)

        if 'Fleet' in writer.book.sheetnames:
            start_row = writer.sheets['Fleet'].max_row
            weight_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Fleet')
            writer.save()
        else:
            weight_df.to_excel(writer, index=False, sheet_name='Fleet')
            writer.save()


def save_station_cap_output(day, sim_heur, base, station_cap, writer):
    df = pd.DataFrame(columns=['Day', 'Total_requests', 'Station capacity', 'Base starvations', 'Base congestions',
                               'Heuristic starvations', 'Heuristic congestions'])

    new_row = {'Day': day, 'Total_requests': sim_heur.total_gen_trips, 'Station capacity': station_cap,
               'Base starvations': base.total_starvations, 'Base congestions': base.total_congestions,
               'Heuristic starvations': sim_heur.total_starvations,
               'Heuristic congestions': sim_heur.total_congestions}

    weight_df = df.append(new_row, ignore_index=True)

    if 'Compare_cap_strategies' in writer.book.sheetnames:
        start_row = writer.sheets['Compare_cap_strategies'].max_row
        weight_df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Compare_cap_strategies')
        writer.save()
    else:
        weight_df.to_excel(writer, index=False, sheet_name='Compare_cap_strategies')
        writer.save()
