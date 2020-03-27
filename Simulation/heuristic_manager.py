from Input.preprocess import generate_all_stations
from Subproblem.model_manager import ModelManager
from vehicle import Vehicle
import numpy as np


class HeuristicManager:

    stations = generate_all_stations('A')
    time_h = 25

    def __init__(self, vehicles):
        self.customer_arrival_scenarios = list()
        self.generate_scenarios()
        self.vehicles = vehicles

        self.run_subproblems()

        self.master_columns = None  # Save output from all subproblems and run master problem

    def run_subproblems(self):
        for vehicle in self.vehicles:
            model_man = ModelManager(HeuristicManager.stations[3], HeuristicManager.stations,
                                     self.customer_arrival_scenarios, vehicle)
            model_man.run_all_subproblems()

    def generate_scenarios(self):
        for station in HeuristicManager.stations:
            c1_times = HeuristicManager.poisson_simulation(station.incoming_charged_bike_rate, HeuristicManager.time_h)
            c2_times = HeuristicManager.poisson_simulation(station.incoming_flat_bike_rate, HeuristicManager.time_h)
            c3_times = HeuristicManager.poisson_simulation(station.outgoing_charged_bike_rate, HeuristicManager.time_h)
            self.customer_arrival_scenarios.append([c1_times, c2_times, c3_times])

    @staticmethod
    def get_index(station_id):
        for i in range(len(HeuristicManager.stations)):
            if HeuristicManager.stations[i].id == station_id:
                return i

    @staticmethod
    def poisson_simulation(intensity_rate, time_steps):
        times = list()
        for t in range(time_steps):
            arrival = np.random.poisson(intensity_rate * time_steps)
            for i in range(arrival):
                times.append(t)
        return times


heuristic_man = HeuristicManager([Vehicle(init_battery_load=15, init_charged_bikes=5, init_flat_bikes=5)])
