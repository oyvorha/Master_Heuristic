from generate_column import *
import numpy as np


class ModelManager:

    stations = generate_all_stations('A')

    def __init__(self, start_station_id):
        self.gen = GenerateColumns(start_station_id, ModelManager.stations)

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
