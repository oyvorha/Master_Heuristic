import numpy as np


class ParameterSub:

    def __init__(self, route_stations, vehicle, pattern, customer_arrivals, base_violations):
        self.A_matrix = ParameterSub.create_A_matrix_subproblem(route_stations)

        # Pattern
        self.Q_B = pattern[0]
        self.Q_CCL = pattern[1]
        self.Q_FCL = pattern[2]
        self.Q_CCU = pattern[3]
        self.Q_FCU = pattern[4]

        # Station specific
        self.Q_S = [station.station_cap for station in route_stations]
        self.L_CS = [station.init_battery_station_load for station in route_stations]
        self.L_FS = [station.init_flat_station_load for station in route_stations]
        self.I_IC = [customer_arrivals[i][0] for i in range(len(customer_arrivals))]
        self.I_FC = [customer_arrivals[i][1] for i in range(len(customer_arrivals))]
        self.I_OC = [customer_arrivals[i][2] for i in range(len(customer_arrivals))]

        # Vehicle specific
        self.Q_BV = vehicle.battery_capacity
        self.Q_CV = vehicle.bike_capacity
        self.L_BV = vehicle.current_batteries
        self.L_CV = vehicle.current_battery_bikes
        self.L_FV = vehicle.current_battery_bikes

        # Base Violations
        self.V_TS = [base_violations[i][0] for i in range(len(base_violations))]
        self.V_TC = [base_violations[i][1] for i in range(len(base_violations))]
        self.V_TbarS = [base_violations[i][2] for i in range(len(base_violations))]
        self.V_TbarC = [base_violations[i][3] for i in range(len(base_violations))]

        # Weights
        self.W_V = 1

    @staticmethod
    def create_A_matrix_subproblem(route_stations):
        A = np.zeros((len(route_stations), len(route_stations)))
        for i in range(len(route_stations) - 1):
            A[i][i + 1] = 1
        return A
