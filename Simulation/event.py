import random
from Simulation.heuristic_manager import HeuristicManager
import time


class Event:

    handling_time = 0.5
    parking_time = 1
    id = 0

    def __init__(self, start_time):
        self.id = Event.id
        Event.id += 1
        self.start_time = start_time
        self.end_time = None
        self.event_time = 0

    def arrival_handling(self):
        pass


class VehicleEvent(Event):

    def __init__(self, start_time, end_time, vehicle, environment, greedy=False):
        Event.__init__(self, start_time)
        self.vehicle = vehicle
        self.env = environment
        self.end_time = end_time
        self.greedy = greedy

    def arrival_handling(self):
        if self.greedy:
            self.greedy_solve()
        else:
            self.heuristic_solve()

    def greedy_solve(self):
        hour = self.env.current_time // 60
        no_vehicles = len(self.env.vehicles)
        splits = len(self.env.stations) // no_vehicles
        next_st_candidates = self.vehicle.current_station.get_candidate_stations(
            self.env.stations[self.vehicle.id*splits:(self.vehicle.id+1)*splits] + [self.env.stations[4]])
        next_station = next_st_candidates[random.randint(0, len(next_st_candidates) - 1)][0]
        swaps = min(self.vehicle.current_batteries, self.vehicle.current_station.current_flat_bikes)
        self.vehicle.current_batteries -= swaps
        self.vehicle.current_station.current_flat_bikes -= swaps
        self.vehicle.current_station.current_charged_bikes += swaps
        bat_load, bat_unload, flat_load, flat_unload = (0, 0, 0, 0)
        if self.vehicle.current_station.current_charged_bikes - self.vehicle.current_station.get_ideal_state(hour) > 0:
            bat_load = max(0, min(self.vehicle.current_station.current_charged_bikes,
                                  self.vehicle.available_bike_capacity(),
                                  self.vehicle.current_station.current_charged_bikes - self.vehicle.current_station.get_ideal_state(
                                      hour)))
            self.vehicle.current_station.current_charged_bikes -= bat_load
            self.vehicle.current_charged_bikes += bat_load
        else:
            bat_unload = max(0,
                             min(self.vehicle.current_charged_bikes, self.vehicle.current_station.available_parking(),
                                 self.vehicle.current_station.get_ideal_state(
                                     hour) - self.vehicle.current_station.current_charged_bikes))
            self.vehicle.current_station.current_charged_bikes += bat_unload
            self.vehicle.current_charged_bikes -= bat_unload
        if self.vehicle.current_station.charging_station:
            flat_unload = min(self.vehicle.current_flat_bikes, self.vehicle.current_station.available_parking())
            self.vehicle.current_station.current_charged_bikes += flat_unload
            self.vehicle.current_flat_bikes -= flat_unload
        else:
            flat_load = min(self.vehicle.current_station.current_flat_bikes, self.vehicle.available_bike_capacity())
            self.vehicle.current_station.current_flat_bikes -= flat_load
            self.vehicle.current_flat_bikes += flat_load
        handling_time = (swaps + flat_load + flat_unload + bat_unload + bat_load) * Event.handling_time
        driving_time = self.vehicle.current_station.get_station_car_travel_time(next_station.id)
        self.vehicle.current_station = next_station
        end_time = self.env.current_time + driving_time + handling_time + Event.parking_time
        self.env.trigger_stack.append(VehicleEvent(self.env.current_time, end_time, self.vehicle, self.env, self.greedy))
        self.env.trigger_stack = sorted(self.env.trigger_stack, key=lambda l: l.end_time)

    def heuristic_solve(self):
        hour = self.env.current_time // 60
        start = time.time()
        heuristic_man = HeuristicManager(self.env.vehicles, self.env.stations, hour,
                                         no_scenarios=self.env.scenarios, init_branching=self.env.init_branching,
                                         weights=self.env.weights, crit_weights=self.env.crit_weights)
        self.event_time = time.time() - start

        # Index of vehicle that triggered event
        next_station, pattern = heuristic_man.return_solution(vehicle_index=self.vehicle.id)

        driving_time = self.vehicle.current_station.get_station_car_travel_time(next_station.id)
        net_charged = abs(pattern[1] - pattern[3])
        net_flat = abs(pattern[2] - pattern[4])
        handling_time = (pattern[0] + net_charged + net_flat) * Event.handling_time
        end_time = driving_time + handling_time + self.env.current_time + Event.parking_time
        self.env.vehicle_vis[self.vehicle.id][0].append(next_station.id)
        self.env.vehicle_vis[self.vehicle.id][1].append([self.vehicle.current_charged_bikes,
                                                         self.vehicle.current_flat_bikes, self.vehicle.current_batteries])
        self.env.vehicle_vis[self.vehicle.id][2].append(pattern)
        self.env.vehicle_vis[self.vehicle.id][3].append([self.vehicle.current_station.current_charged_bikes,
                                                         self.vehicle.current_station.current_flat_bikes])
        self.update_decision(self.vehicle, self.vehicle.current_station, pattern, next_station)
        self.env.trigger_stack.append(
            VehicleEvent(self.env.current_time, end_time, self.vehicle, self.env, self.greedy))
        self.env.trigger_stack = sorted(self.env.trigger_stack, key=lambda l: l.end_time)

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
            station.change_flat_load(-Q_FCL + Q_FCU - Q_B)
        if station.depot:
            vehicle.current_batteries = vehicle.battery_capacity
