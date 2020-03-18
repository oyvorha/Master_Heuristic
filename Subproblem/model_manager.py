from generate_route_pattern import generate_all_stations, GenerateRoutePattern
from parameters_subproblem import ParameterSub
from vehicle import Vehicle
from subproblem_model import run_model
import numpy as np
import random


class ModelManager:

    stations = generate_all_stations('A')[:10]
    starvation_list = []
    congestion_list = []

    def __init__(self, start_station_id, vehicle=Vehicle(5, 5, 5)):
        self.starting_station = ModelManager.stations[ModelManager.get_index(start_station_id)]
        self.vehicle = vehicle
        self.gen = GenerateRoutePattern(self.starting_station, ModelManager.stations, vehicle)
        self.congestion_list = None
        self.starvation_list = None

    def run_one_subproblem(self, route, pattern):
        customer_arrivals = ModelManager.poisson_draw(route)
        base_viol = [[5, 10, 15, 5] for i in range(len(route.stations))]
        params = ParameterSub(route.stations, self.vehicle, pattern, customer_arrivals, base_viol)
        run_model(params)

    @staticmethod
    def create_A_matrix(column):
        A = np.zeros((len(ModelManager.stations), len(ModelManager.stations)))
        route = [st.id for st in column.stations]
        for i in range(len(route)-1):
            st1 = ModelManager.get_index(route[i])
            st2 = ModelManager.get_index(route[i+1])
            A[st1][st2] = 1
        return A

    @staticmethod
    def get_index(station_id):
        for i in range(len(ModelManager.stations)):
            if ModelManager.stations[i] == station_id:
                return i

    @staticmethod
    def poisson_draw(route):
        # Returns Poisson draw for incoming charged bikes, incoming flat bikes, outgoing charged bikes at time of visit
        arrivals = list()
        for i in range(len(route.stations)):
            st_arrivals = list()
            st_arrivals.append(np.random.poisson(route.stations[i].incoming_charged_bike_rate * route.station_visits[i]))
            st_arrivals.append(np.random.poisson(route.stations[i].incoming_flat_bike_rate * route.station_visits[i]))
            st_arrivals.append(np.random.poisson(route.stations[i].outgoing_charged_bike_rate * route.station_visits[i]))
            arrivals.append(st_arrivals)
        return arrivals

    def get_violations(self):
        starvation_list = []
        congestion_list = []
        for station in ModelManager.stations:
            violation_starvation = 0
            violation_congestion = 0
            batt_load_timehorizon = random.randint(-10, 10)  # edit to poisson process draw
            flat_load_timehorizon = random.randint(0, 10)  # edit to poisson process draw
            real_batt_load = batt_load_timehorizon
            real_flat_load = flat_load_timehorizon
            if batt_load_timehorizon < 0:
                violation_starvation = -batt_load_timehorizon
                real_batt_load = 0
            if real_batt_load + real_flat_load > 12:  # change 12 to station cap
                violation_congestion = real_batt_load + real_flat_load - 12  # change 12 to station cap
            starvation_list.append(violation_starvation)
            congestion_list.append(violation_congestion)
        self.starvation_list = starvation_list
        self.congestion_list = congestion_list
