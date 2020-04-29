from Input.preprocess import generate_all_stations, get_driving_time_from_id
from vehicle import Vehicle
from Simulation.heuristic_manager import HeuristicManager
import json
import random
import time
import copy
from Output.save_to_excel import save_time_output


class Environment:

    simulation_time = 0.1
    handling_time = 0.3
    parking_time = 2

    def __init__(self, start_time, no_stations, vehicles, init_branching, scenarios, shadow=False):
        self.stations = generate_all_stations('A')[:no_stations]
        self.stations[4].depot = True
        self.vehicles = vehicles
        for veh1 in vehicles:
            veh1.current_station = self.stations[veh1.id]
        self.current_time = start_time
        self.trigger_stack = [[0, self.vehicles[j]] for j in range(len(self.vehicles))]
        self.shadow_vehicles = list()
        if shadow:
            self.shadow_vehicles = copy.deepcopy(vehicles)
            for v in self.shadow_vehicles:
                self.trigger_stack.append([0, v])
        self.vehicle_vis = {v.id: [[v.current_station.id], [], [], []] for v in self.vehicles}
        self.total_starvations = 0
        self.total_congestions = 0
        self.total_shadow_starvations = 0
        self.total_shadow_congestions = 0
        self.base_starvations = 0
        self.base_congestions = 0
        self.init_branching = init_branching
        self.scenarios = scenarios
        self.single_time = 0

        self.print_number_of_bikes()
        while self.trigger_stack[0][0] < Environment.simulation_time:
            self.event_trigger()
        self.print_number_of_bikes()
        self.print_status()
        self.visualize_system()

    def event_trigger(self):
        event = self.trigger_stack.pop(0)
        time_since_last_event = event[0] - self.current_time
        self.current_time = event[0]
        self.update_system(time_since_last_event)
        vehicle_trigger = event[1]
        if vehicle_trigger in self.shadow_vehicles:
            self.greedy_solve(vehicle_trigger)
        else:
            self.heuristic_solve(vehicle_trigger)

    def greedy_solve(self, veh):
        next_st_candidates = veh.current_station.get_candidate_stations(self.stations)
        next_station = next_st_candidates[random.randint(0, len(next_st_candidates)-1)][0]
        swaps = min(veh.current_batteries, veh.current_station.shadow_current_flat_bikes)
        veh.current_batteries -= swaps
        veh.current_station.shadow_current_flat_bikes -= swaps
        veh.current_station.shadow_current_charged_bikes += swaps
        if veh.current_station.charging_station:
            net_charged = min(veh.current_station.shadow_current_charged_bikes, veh.available_bike_capacity())
            veh.current_station.shadow_current_charged_bikes -= net_charged
            veh.current_charged_bikes += net_charged
            net_flat = min(veh.current_flat_bikes, veh.current_station.get_shadow_parking())
            veh.current_station.shadow_current_charged_bikes += net_flat
            veh.current_flat_bikes -= net_flat
        else:
            net_charged = min(veh.current_station.get_shadow_parking(), veh.current_charged_bikes)
            veh.current_station.shadow_current_charged_bikes += net_charged
            veh.current_charged_bikes -= net_charged
            net_flat = min(veh.current_station.shadow_current_flat_bikes, veh.available_bike_capacity())
            veh.current_station.shadow_current_flat_bikes -= net_flat
            veh.current_flat_bikes += net_flat
        handling_time = (swaps + net_flat + net_charged) * Environment.handling_time
        driving_time = get_driving_time_from_id(veh.current_station.id, next_station.id)[0]
        veh.current_station = next_station
        self.trigger_stack.append([self.current_time + driving_time + handling_time + Environment.parking_time, veh])
        self.trigger_stack = sorted(self.trigger_stack, key=lambda l: l[0])

    def heuristic_solve(self, veh):
        start = time.time()
        heuristic_man = HeuristicManager(self.vehicles, self.stations,
                                         no_scenarios=self.scenarios, init_branching=self.init_branching)
        self.single_time = time.time() - start

        # Index of vehicle that triggered event
        next_station, pattern = heuristic_man.return_solution(vehicle_index=veh.id)
        driving_time = get_driving_time_from_id(veh.current_station.id, next_station.id)[0]
        net_charged = abs(pattern[1] - pattern[3])
        net_flat = abs(pattern[2] - pattern[4])
        handling_time = (pattern[0] + net_charged + net_flat) * Environment.handling_time

        self.trigger_stack.append([self.current_time + driving_time + handling_time + Environment.parking_time, veh])
        self.trigger_stack = sorted(self.trigger_stack, key=lambda l: l[0])
        self.vehicle_vis[veh.id][0].append(next_station.id)
        self.vehicle_vis[veh.id][1].append([veh.current_charged_bikes,
                                            veh.current_flat_bikes, veh.current_batteries])
        self.vehicle_vis[veh.id][2].append(pattern)
        self.vehicle_vis[veh.id][3].append([veh.current_station.current_charged_bikes,
                                            veh.current_station.current_flat_bikes])
        self.update_decision(veh, veh.current_station, pattern, next_station)

    def update_decision(self, vehicle, station, pattern, next_station):
        Q_B, Q_CCL, Q_FCL, Q_CCU, Q_FCU = pattern[0], pattern[1], pattern[2], pattern[3], pattern[4]
        vehicle.change_battery_bikes(-Q_CCU + Q_CCL)
        vehicle.change_flat_bikes(-Q_FCU + Q_FCL)
        vehicle.swap_batteries(Q_B)
        vehicle.current_station = next_station
        station.change_charged_load(-Q_CCL + Q_CCU + Q_B)
        if station.charging_station:  # If charging station, make flat unload battery unload immediately
            station.change_charged_load(-Q_FCL + Q_FCU)
        else:
            station.change_flat_load(-Q_FCL + Q_FCU)
        if station.depot:
            vehicle.current_batteries = vehicle.battery_capacity

    def update_system(self, elaps_time):
        elapsed_time = int(elaps_time)
        for station in self.stations:
            if not station.depot:
                L_CS = station.current_charged_bikes
                L_FS = station.current_flat_bikes
                L_CS_shadow = station.shadow_current_charged_bikes
                L_FS_shadow = station.shadow_current_flat_bikes
                L_CS_base = station.base_current_charged_bikes
                L_FS_base = station.base_current_flat_bikes
                incoming_charged_bike_times = HeuristicManager.poisson_simulation(station.incoming_charged_bike_rate,
                                                                                  elapsed_time)
                incoming_flat_bike_times = HeuristicManager.poisson_simulation(station.incoming_flat_bike_rate,
                                                                               elapsed_time)
                outgoing_charged_bike_times = HeuristicManager.poisson_simulation(station.outgoing_charged_bike_rate,
                                                                                  elapsed_time)
                for i in range(elapsed_time):
                    c1 = incoming_charged_bike_times.count(i)
                    c2 = incoming_flat_bike_times.count(i)
                    c3 = outgoing_charged_bike_times.count(i)
                    self.base_starvations -= min(0, L_CS_base + c1 - c3)
                    L_CS_base = max(0, min(station.station_cap - L_FS_base, L_CS_base + c1 - c3))
                    self.base_congestions += max(0, L_FS_base + L_CS_base + c2 - station.station_cap)
                    L_FS_base = min(station.station_cap - L_CS_base, L_FS_base + c2)
                    self.total_starvations -= min(0, L_CS + c1 - c3)
                    L_CS = max(0, min(station.station_cap - L_FS, L_CS + c1 - c3))
                    self.total_congestions += max(0, L_FS + L_CS + c2 - station.station_cap)
                    L_FS = min(station.station_cap - L_CS, L_FS + c2)
                    self.total_shadow_starvations -= min(0, L_CS_shadow + c1 - c3)
                    L_CS_shadow = max(0, min(station.station_cap - L_FS_shadow, L_CS_shadow + c1 - c3))
                    self.total_shadow_congestions += max(0, L_FS_shadow + L_CS_shadow + c2 - station.station_cap)
                    L_FS_shadow = min(station.station_cap - L_CS_shadow, L_FS_shadow + c2)
                station.current_charged_bikes = L_CS
                station.current_flat_bikes = L_FS
                station.base_current_charged_bikes = L_CS_base
                station.base_current_flat_bikes = L_FS_base
                station.shadow_current_charged_bikes = L_CS_shadow
                station.shadow_current_flat_bikes = L_FS_shadow

    def visualize_system(self):
        json_stations = {}
        for station in self.stations:
            # [lat, long], charged bikes, flat bikes, starvation score, congestion score
            json_stations[station.id] = [[station.latitude, station.longitude], station.current_charged_bikes,
                                         station.current_flat_bikes, int(station.charging_station), int(station.depot) * 5]
        with open('../Visualization/station_vis.json', 'w') as fp:
            json.dump(json_stations, fp)
        with open('../Visualization/vehicle.json', 'w') as f:
            json.dump(self.vehicle_vis, f)

    def print_status(self):
        print("--------------------- SIMULATION STATUS -----------------------")
        print("Simulation time =", Environment.simulation_time, "minutes")
        print("Starvations =", self.total_starvations)
        print("Congestions =", self.total_congestions)
        print("Shadow Starvations =", self.total_shadow_starvations)
        print("Shadow Congestions =", self.total_shadow_congestions)
        print("BASE Starvations =", self.base_starvations)
        print("BASE Congestions =", self.base_congestions)

    def print_number_of_bikes(self):
        total_charged = 0
        total_flat = 0
        for station in self.stations:
            total_charged += station.current_charged_bikes
            total_flat += station.current_flat_bikes
        print("Total charged: ", total_charged)
        print("Total flat: ", total_flat)


def run_solution_time_analysis():
    for scenarios in [20, 30, 40, 50]:
        for vehicles in [1, 2, 3, 4, 5]:
            veh = list()
            for i in range(vehicles):
                veh.append(Vehicle(init_battery_load=10, init_charged_bikes=10, init_flat_bikes=10, current_station=None, id=i))
            for branching in [1, 2, 3, 4, 5, 6]:
                for stations in [10, 30, 50, 70]:
                    env = Environment(0, stations, veh, branching, scenarios)
                    save_time_output(stations, branching, scenarios, vehicles, env.single_time)
                    print("OUTPUT SAVED: ", scenarios, vehicles, branching, stations)


if __name__ == '__main__':
    run_solution_time_analysis()
    """
    # Single run
    stations = 50
    veh = [Vehicle(init_battery_load=10, init_charged_bikes=10, init_flat_bikes=10, current_station=None, id=0)]
    branching = 6
    scenarios = 1
    env = Environment(0, stations, veh, branching, scenarios, shadow=True)
    """
