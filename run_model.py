from generate_route_pattern import *
import numpy as np
import random


class ModelManager:

    stations = generate_all_stations('A')
    starvation_list = []
    congestion_list = []

    def __init__(self, start_station_id):
        self.gen = GenerateRoutePattern(start_station_id, ModelManager.stations)
        self.congestion_list = None
        self.starvation_list = None

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
