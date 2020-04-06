from Input.preprocess import generate_all_stations
from Subproblem.model_manager import ModelManager
from Subproblem.generate_route_pattern import GenerateRoutePattern
from vehicle import Vehicle
import numpy as np
from MasterProblem.master_params import MasterParameters
from MasterProblem.master_model import run_master_model


class HeuristicManager:

    stations = generate_all_stations('A')
    time_h = 25

    def __init__(self, vehicles):
        self.customer_arrival_scenarios = list()
        self.generate_scenarios()
        self.vehicles = vehicles

        self.route_patterns = list()
        self.subproblem_scores = list()

        self.run_subproblems()
        self.run_master_problem()

    def run_vehicle_subproblems(self, vehicle):
        gen = GenerateRoutePattern(vehicle.current_station, HeuristicManager.stations, vehicle)
        gen.get_columns()
        self.route_patterns.append(gen)
        model_man = ModelManager(vehicle)
        route_scores = list()
        for route in gen.finished_gen_routes:
            route_full_set_index = [HeuristicManager.get_index(st.id) for st in route.stations]
            pattern_scores = list()
            for pattern in gen.patterns:
                scenario_scores = list()
                for customer_scenario in self.customer_arrival_scenarios:
                    score = model_man.run_one_subproblem(route, route_full_set_index, pattern, customer_scenario)
                    scenario_scores.append(score)
                pattern_scores.append(scenario_scores)
            route_scores.append(pattern_scores)
        self.subproblem_scores.append(route_scores)

    def run_subproblems(self):
        for vehicle in self.vehicles:
            self.run_vehicle_subproblems(vehicle)
        print(np.shape(self.subproblem_scores))
        print(np.shape(self.route_patterns))

    def run_master_problem(self):
        params = MasterParameters(route_pattern=self.route_patterns, subproblem_scores=self.subproblem_scores,
                                  customer_scenarios=self.customer_arrival_scenarios, heuristic_man=self)
        master_model = run_master_model(params)

    def generate_scenarios(self):
        scenario = list()
        for station in HeuristicManager.stations:
            c1_times = HeuristicManager.poisson_simulation(station.incoming_charged_bike_rate, HeuristicManager.time_h)
            c2_times = HeuristicManager.poisson_simulation(station.incoming_flat_bike_rate, HeuristicManager.time_h)
            c3_times = HeuristicManager.poisson_simulation(station.outgoing_charged_bike_rate, HeuristicManager.time_h)
            scenario.append([c1_times, c2_times, c3_times])
        self.customer_arrival_scenarios.append(scenario)

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


heuristic_man = HeuristicManager([Vehicle(init_battery_load=20, init_charged_bikes=15, init_flat_bikes=1,
                                          current_station=HeuristicManager.stations[3])])
