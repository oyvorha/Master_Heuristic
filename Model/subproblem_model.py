from gurobipy import *
import time


def run_model(data):

    try:
        m = Model("Heuristic")
        m.setParam('TimeLimit', 60 * 60)
        start_time = time.time()

        # ------ SETS -----------------------------------------------------------------------------
        Stations = data.stations
        Charging_stations = data.stations
        Non_Charging_stations = data.stations
        Swap_Stations = Stations[1:-1]

        # ------ PARAMETERS -----------------------------------------------------------------------
        A = data.matrix

    except GurobiError:
            print("Error")
