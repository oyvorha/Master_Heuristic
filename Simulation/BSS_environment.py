from Input.preprocess import generate_all_stations, get_driving_time_from_id
from vehicle import Vehicle
from Simulation.heuristic_manager import HeuristicManager
import json


class Environment:

    stations = generate_all_stations('A')
    simulation_time = 60
    vehicles = [Vehicle(init_battery_load=20, init_charged_bikes=15, init_flat_bikes=1,
                current_station=stations[3], id=0), Vehicle(init_battery_load=20, init_charged_bikes=15, init_flat_bikes=1,
                current_station=stations[10], id=1)]
    handling_time = 0.3

    def __init__(self, start_time):
        self.current_time = start_time
        self.trigger_stack = [[0, Environment.vehicles[0]], [6, Environment.vehicles[1]]]
        self.vehicle_vis = {v.id: [[0, 0, 0, 0, 0], v.current_station] for v in Environment.vehicles}
        self.total_starvations = 0
        self.total_congestions = 0

        while self.current_time < Environment.simulation_time:
            self.event_trigger()
        self.print_status()

    def event_trigger(self):
        event = self.trigger_stack.pop(0)
        time_since_last_event = event[0] - self.current_time
        self.current_time = event[0]
        self.update_system(time_since_last_event)
        vehicle_trigger = event[1]
        self.heuristic_solve(vehicle_trigger)

    def heuristic_solve(self, veh):
        heuristic_man = HeuristicManager(Environment.vehicles, Environment.stations)

        # Index of vehicle that triggered event
        next_station, pattern = heuristic_man.return_solution(vehicle_index=veh.id)
        driving_time = get_driving_time_from_id(veh.current_station.id, next_station.id)[0]
        net_charged = abs(pattern[1] - pattern[3])
        net_flat = abs(pattern[2] - pattern[4])
        handling_time = (pattern[0] + net_charged + net_flat) * Environment.handling_time

        self.trigger_stack.append([self.current_time + driving_time + handling_time, veh])
        self.trigger_stack = sorted(self.trigger_stack, key=lambda l: l[0])
        print(self.trigger_stack)
        self.vehicle_vis[veh.id] = [pattern, next_station]
        self.visualize_system()
        self.update_decision(veh, veh.current_station, pattern, next_station)

    def update_decision(self, vehicle, station, pattern, next_station):
        Q_B, Q_CCL, Q_FCL, Q_CCU, Q_FCU = pattern[0], pattern[1], pattern[2], pattern[3], pattern[4]
        vehicle.change_battery_bikes(-Q_CCU + Q_CCL)
        vehicle.change_flat_bikes(-Q_FCU + Q_FCL)
        vehicle.swap_batteries(Q_B)
        vehicle.current_station = next_station
        station.change_charged_load(-Q_CCL + Q_CCU + Q_B)
        station.change_flat_load(-Q_FCL + Q_FCU)

    def update_system(self, elaps_time):
        elapsed_time = int(elaps_time)
        for station in Environment.stations:
            L_CS = station.current_charged_bikes
            L_FS = station.current_flat_bikes
            incoming_charged_bike_times = HeuristicManager.poisson_simulation(station.incoming_charged_bike_rate, elapsed_time)
            incoming_flat_bike_times = HeuristicManager.poisson_simulation(station.incoming_flat_bike_rate, elapsed_time)
            outgoing_charged_bike_times = HeuristicManager.poisson_simulation(station.outgoing_charged_bike_rate, elapsed_time)
            for i in range(elapsed_time):
                c1 = incoming_charged_bike_times.count(i)
                c2 = incoming_flat_bike_times.count(i)
                c3 = outgoing_charged_bike_times.count(i)
                minute_starvations = min(0, L_CS + c1 - c3)
                self.total_starvations -= minute_starvations
                L_CS = max(0, min(station.station_cap - L_FS, L_CS + c1 - c3))
                self.total_congestions += max(0, L_FS + L_CS + c2 - minute_starvations - station.station_cap)
                L_FS = min(station.station_cap - L_CS, L_FS + c2)
            station.current_charged_bikes = L_CS
            station.current_flat_bikes = L_FS

    def visualize_system(self):
        json_stations = {}
        for station in Environment.stations:
            # [lat, long], charged bikes, flat bikes, starvation score, congestion score
            json_stations[station.id] = [[station.latitude, station.longitude], station.current_charged_bikes,
                                         station.current_flat_bikes, 0, 0]
        with open('../Visualization/station_vis.json', 'w') as fp:
            json.dump(json_stations, fp)

        vehicle_json = {}
        v = Environment.vehicles
        for i in range(len(v)):
            vehicle_json[str(i)] = [[v[i].current_station.latitude, v[i].current_station.longitude],
                                    v[i].current_charged_bikes, v[i].current_flat_bikes, v[i].current_batteries,
                                    self.vehicle_vis[i][1].id, self.vehicle_vis[i][0]]
        with open('../Visualization/vehicle.json', 'w') as f:
            json.dump(vehicle_json, f)

    def print_status(self):
        print("--------------------- SIMULATION STATUS -----------------------")
        print("Simulation time =", Environment.simulation_time, "minutes")
        print("Starvations =", self.total_starvations)
        print("Congestions =", self.total_congestions)


env = Environment(0)
