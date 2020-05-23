from Input.preprocess import generate_all_stations, reset_stations
from vehicle import Vehicle
from Output.save_to_excel import save_time_output, save_weight_output
from Simulation.BSS_environment import Environment
import copy


def run_solution_time_analysis():
    for scenario in [20, 30, 40, 50]:
        for vehicles in [1, 2, 3, 4, 5]:
            veh = list()
            for i in range(vehicles):
                veh.append(Vehicle(init_battery_load=10, init_charged_bikes=10, init_flat_bikes=10, current_station=None, id=i))
            for branching in [1, 2, 3, 4, 5, 6]:
                for stations in [10, 30, 50, 70]:
                    # env = Environment(0, stations, veh, branching, scenario, scenarios)
                    # save_time_output(stations, branching, scenarios, vehicles, env.event_times)
                    print("OUTPUT SAVED")


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
    print(len(w), w)
    # return weights
    return [(0.6, 0.3, 0.1, 0.7, 0.3)]


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
    print(len(w), w)
    # return weights
    return w


def weight_analysis():
    start_hour = 7
    no_stations = 200
    branching = 3
    subproblem_scenarios = 3
    simulation_time = 960  # 7 am to 11 pm
    stations = generate_all_stations(start_hour, no_stations)
    stations[4].depot = True
    all_sets = get_weight_combination_reduced()
    veh = Vehicle(init_battery_load=20, init_charged_bikes=20, init_flat_bikes=0, current_station=stations[0], id=0)
    env = Environment(start_hour, simulation_time, stations, [veh], branching, subproblem_scenarios)

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
            print("Output saved")
            reset_stations(stations)


if __name__ == '__main__':
    weight_analysis()
    """
    # run_solution_time_analysis()
    # Single run
    start_hour = 7
    no_stations = 200
    branching = 3
    scenarios = 3
    simulation_time = 60  # Set this to value divisible by 60
    stations = generate_all_stations(start_hour, no_stations)
    stations[4].depot = True
    veh1 = Vehicle(init_battery_load=20, init_charged_bikes=20, init_flat_bikes=0, current_station=stations[0], id=0)
    veh3 = Vehicle(init_battery_load=30, init_charged_bikes=30, init_flat_bikes=0, current_station=stations[0], id=0)
    env_base = Environment(start_hour, simulation_time, stations, list(), branching, scenarios)
    stack_base = [copy.copy(trip) for trip in env_base.initial_stack]
    reset_stations(stations)
    env3 = Environment(start_hour, simulation_time, stations, [veh3], branching, scenarios,
                       trigger_start_stack=env_base.initial_stack, memory_mode=True,
                       greedy=True)
    reset_stations(stations)
    env = Environment(start_hour, simulation_time, stations, [veh1], branching, scenarios, trigger_start_stack=stack_base,
                      memory_mode=True, greedy=False)
    print("----- SIMULATION COMPARISON ---------")
    print("Simulation time =", simulation_time, "minutes")
    print("Total requested trips =", env.total_gen_trips)
    print("Starvations base=", env_base.total_starvations)
    print("Congestions base=", env_base.total_congestions)
    print("Starvations greedy=", env3.total_starvations)
    print("Congestions greedy=", env3.total_congestions)
    print("Starvations heur=", env.total_starvations)
    print("Congestions heur=", env.total_congestions)
    """