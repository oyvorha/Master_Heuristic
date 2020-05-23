from Input.preprocess import generate_all_stations, reset_stations
from vehicle import Vehicle
from Output.save_to_excel import save_weight_output, save_comparison_output
from Simulation.BSS_environment import Environment
import copy


start_hour = 7
no_stations = 200
branching = 3
subproblem_scenarios = 3
simulation_time = 960  # 7 am to 11 pm
stations = generate_all_stations(start_hour, no_stations)
stations[4].depot = True


def get_weight_combination():
    # W_V, W_R, W_D, W_VN, W_VL
    weights = list()
    vals = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    for val1 in vals:
        W_V = val1
        for val2 in vals:
            if W_V + val2 <= 1:
                W_R = val2
            else:
                W_R = 0
            W_D = 1 - W_R - W_V
            for val3 in vals:
                W_VN = val3
                W_VL = 1 - W_VN
                weights.append((W_V, W_R, W_D, W_VN, W_VL))
    w = list(set(tuple(val) for val in weights))
    return w


def get_weight_combination_reduced():
    # W_V, W_R, W_D, W_VN, W_VL
    weights = list()
    vals = [0, 0.25, 0.5, 0.75, 1]
    W_VN = 0.75
    W_VL = 0.25
    for val1 in vals:
        W_V = val1
        for val2 in vals:
            if W_V + val2 <= 1:
                W_R = val2
            else:
                W_R = 0
            W_D = 1 - W_R - W_V
            weights.append((W_V, W_R, W_D, W_VN, W_VL))
    w = list(set(tuple(val) for val in weights))
    return w


def weight_analysis():
    all_sets = get_weight_combination_reduced()
    env = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios)

    # Generating 10 scenarios
    scenarios = [env.generate_trips(simulation_time//60, gen=True) for i in range(3)]
    print([len(sc) for sc in scenarios])

    base_s = list()
    base_c = list()

    for w in all_sets:
        w_base_s = list()
        w_base_c = list()
        for sc in scenarios:
            init_base_stack = [copy.copy(trip) for trip in sc]
            sim_base = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios,
                                   trigger_start_stack=init_base_stack, memory_mode=True, weights=w)
            sim_base.run_simulation()
            w_base_s.append(sim_base.total_starvations)
            w_base_c.append(sim_base.total_congestions)
            reset_stations(stations)
        base_s.append(w_base_s)
        base_c.append(w_base_c)

    for i in range(len(all_sets)):
        for j in range(len(scenarios)):
            reset_stations(stations)
            init_stack = [copy.copy(trip) for trip in scenarios[j]]
            v = Vehicle(init_battery_load=20, init_charged_bikes=20, init_flat_bikes=0, current_station=stations[0],
                          id=0)
            sim_env = Environment(start_hour, simulation_time, stations, [v], branching, subproblem_scenarios,
                                  trigger_start_stack=init_stack, memory_mode=True, weights=all_sets[i])
            sim_env.run_simulation()
            save_weight_output(i+1, j+1, sim_env, base_s[i][j], base_c[i][j])


def strategy_analysis():
    vehicles = list()
    for i in range(3):
        vehicles.append(Vehicle(init_battery_load=40, init_charged_bikes=20, init_flat_bikes=0,
                                current_station=stations[i], id=i))
    env = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios)

    # Generating 10 scenarios
    scenarios = [env.generate_trips(simulation_time//60, gen=True) for i in range(2)]

    scenario = 1
    for sc in scenarios:
        init_base_stack = [copy.copy(trip) for trip in sc]
        sim_base = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios,
                               trigger_start_stack=init_base_stack, memory_mode=True)
        sim_base.run_simulation()
        reset_stations(stations)
        init_greedy_stack = [copy.copy(trip) for trip in sc]
        vehicles_greedy = [copy.copy(veh) for veh in vehicles]
        sim_greedy = Environment(start_hour, simulation_time, stations, vehicles_greedy, branching,
                                 subproblem_scenarios, trigger_start_stack=init_greedy_stack, memory_mode=True,
                                 greedy=True)
        sim_greedy.run_simulation()
        reset_stations(stations)
        init_heur_stack = [copy.copy(trip) for trip in sc]
        vehicles_heur = [copy.copy(veh) for veh in vehicles]
        sim_heur = Environment(start_hour, simulation_time, stations, vehicles_heur, branching,
                                 subproblem_scenarios, trigger_start_stack=init_heur_stack, memory_mode=True)
        sim_heur.run_simulation()
        reset_stations(stations)
        save_comparison_output(scenario, sim_heur, sim_base.total_starvations, sim_base.total_congestions,
                               sim_greedy.total_starvations, sim_greedy.total_congestions)
        scenario += 1


if __name__ == '__main__':
    print("w: weight analysis, c: strategy comparison, r: runtime analysis")
    choice = input('Choose action: ')
    if choice == 'w':
        weight_analysis()
    elif choice == 'c':
        strategy_analysis()
    else:
        print("No analysis")
