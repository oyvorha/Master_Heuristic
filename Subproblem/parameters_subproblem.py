import numpy as np


class ParameterSub:

    def __init__(self, route_stations, vehicle, pattern, customer_arrivals, L_CS, L_FS, base_violations):
        self.A_matrix = ParameterSub.create_A_matrix_subproblem(route_stations)
        self.stations = [i for i in range(len(route_stations)+2)]
        self.charging_stations = list()
        self.non_charging_stations = list()
        for i in range(len(route_stations)):
            if route_stations[i].charging_station:
                self.charging_stations.append(i+1)
            else:
                self.non_charging_stations.append(i+1)

        # Pattern
        self.Q_B = pattern[0]
        self.Q_CCL = pattern[1]
        self.Q_FCL = pattern[2]
        self.Q_CCU = pattern[3]
        self.Q_FCU = pattern[4]

        # Station specific
        self.Q_S = [0] + [station.station_cap for station in route_stations] + [0]
        self.L_CS = [0] + L_CS + [0]
        self.L_FS = [0] + L_FS + [0]
        self.I_IC = [0] + [customer_arrivals[i][0] for i in range(len(customer_arrivals))] + [0]
        self.I_IF = [0] + [customer_arrivals[i][1] for i in range(len(customer_arrivals))] + [0]
        self.I_OC = [0] + [customer_arrivals[i][2] for i in range(len(customer_arrivals))] + [0]

        # Vehicle specific
        self.Q_BV = vehicle.battery_capacity
        self.Q_CV = vehicle.bike_capacity
        self.L_BV = vehicle.current_batteries
        self.L_CV = vehicle.current_battery_bikes
        self.L_FV = vehicle.current_battery_bikes

        # Base Violations
        self.V_TS = [0] + base_violations + [0]

        # Weights
        self.W_V = 1

    @staticmethod
    def create_A_matrix_subproblem(route_stations):
        A = np.zeros((len(route_stations)+2, len(route_stations)+2))
        for i in range(len(route_stations) + 1):
            A[i][i + 1] = 1
        return A
