import random
from Simulation.heuristic_manager import HeuristicManager
import time
from Output.save_to_excel import save_first_step_solution, criticality_weights
import numpy as np


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
        next_st_candidates = self.vehicle.current_station.get_candidate_stations(self.env.stations)
        next_station = next_st_candidates[random.randint(0, len(next_st_candidates) - 1)][0]
        swaps = min(self.vehicle.current_batteries, self.vehicle.current_station.current_flat_bikes)
        self.env.vehicle_vis[self.vehicle.id][1].append([self.vehicle.current_charged_bikes,
                                                         self.vehicle.current_flat_bikes,
                                                         self.vehicle.current_batteries])
        self.env.vehicle_vis[self.vehicle.id][3].append([self.vehicle.current_station.current_charged_bikes,
                                                         self.vehicle.current_station.current_flat_bikes])
        self.vehicle.current_batteries -= swaps
        self.vehicle.current_station.current_flat_bikes -= swaps
        self.vehicle.current_station.current_charged_bikes += swaps
        if self.vehicle.current_station.charging_station:
            net_charged = min(self.vehicle.current_station.current_charged_bikes, self.vehicle.available_bike_capacity())
            self.vehicle.current_station.current_charged_bikes -= net_charged
            self.vehicle.current_charged_bikes += net_charged
            net_flat = min(self.vehicle.current_flat_bikes, self.vehicle.current_station.available_parking())
            self.vehicle.current_station.current_flat_bikes += net_flat
            self.vehicle.current_flat_bikes -= net_flat
        else:
            net_charged = min(self.vehicle.current_station.available_parking(), self.vehicle.current_charged_bikes)
            self.vehicle.current_station.current_charged_bikes += net_charged
            self.vehicle.current_charged_bikes -= net_charged
            net_flat = min(self.vehicle.current_station.current_flat_bikes, self.vehicle.available_bike_capacity())
            self.vehicle.current_station.current_flat_bikes -= net_flat
            self.vehicle.current_flat_bikes += net_flat
        self.env.vehicle_vis[self.vehicle.id][0].append(next_station.id)
        self.env.vehicle_vis[self.vehicle.id][2].append([swaps, net_charged, net_flat, net_charged, net_flat])
        handling_time = (swaps + net_flat + net_charged) * Event.handling_time
        driving_time = self.vehicle.current_station.get_station_car_travel_time(next_station.id)
        self.vehicle.current_station = next_station
        end_time = self.env.current_time + driving_time + handling_time + Event.parking_time
        self.env.trigger_stack.append(VehicleEvent(self.env.current_time, end_time, self.vehicle, self.env, self.greedy))
        self.env.trigger_stack = sorted(self.env.trigger_stack, key=lambda l: l.end_time)

    def heuristic_solve(self):
        hour = self.env.current_time // 60
        start = time.time()
        c_weights = HeuristicManager.get_criticality_weights()
        heuristic_man = HeuristicManager(self.env.vehicles, self.env.stations, hour,
                                             no_scenarios=self.env.scenarios, init_branching=self.env.init_branching,
                                             weights=self.env.weights, crit_weights=(0.4, 0.1, 0.2, 0.3))

        for i in range(len(c_weights)):
            heuristic_man.reset_manager_and_run(self.env.init_branching, c_weights[i])
            average_subscore = np.average(heuristic_man.subproblem_scores)
            criticality_weights(self.env.current_time, i, c_weights[i][0], c_weights[i][1], c_weights[i][2],
                                c_weights[i][3], average_subscore, self.env.writer)
        """
        
        next_station, pattern = heuristic_man.return_solution(vehicle_index=self.vehicle.id)
        save_first_step_solution(self.id, self.env.init_branching, pattern[0], pattern[1]-pattern[3], pattern[2]-pattern[4],
                                 next_station, self.env.writer, self.vehicle.current_station.get_ideal_state(hour),
                                 self.vehicle.current_station.current_charged_bikes,
                                 self.vehicle.current_station.current_flat_bikes)
        
        for branching in [5]:
            heuristic_man.reset_manager_and_run(branching)
            next_station, pattern = heuristic_man.return_solution(vehicle_index=self.vehicle.id)
            save_first_step_solution(self.id, branching, pattern[0], pattern[1]-pattern[3], pattern[2]-pattern[4],
                                     next_station, self.env.writer, self.vehicle.current_station.get_ideal_state(hour),
                                     self.vehicle.current_station.current_charged_bikes,
                                     self.vehicle.current_station.current_flat_bikes)
        """
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
            station.change_flat_load(-Q_FCL + Q_FCU)
        if station.depot:
            vehicle.current_batteries = vehicle.battery_capacity
