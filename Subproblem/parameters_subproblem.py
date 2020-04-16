
class ParameterSub:

    def __init__(self, route, vehicle, pattern, customer_arrivals, L_CS, L_FS, base_violations, depot=None):
        # Sets
        self.stations = [i for i in range(len(route.stations))]
        self.charging_stations = list()
        self.non_charging_stations = list()
        for i in range(len(route.stations)):
            if route.stations[i].charging_station:
                self.charging_stations.append(i+1)
            else:
                self.non_charging_stations.append(i+1)
        self.depot_index = depot
        self.visits = route.station_visits

        # Pattern
        # Q_B, Q_CCL, Q_FCL, Q_CCU, Q_FCU
        self.Q_B = pattern[0]
        self.Q_CCL = pattern[1]
        self.Q_FCL = pattern[2]
        self.Q_CCU = pattern[3]
        self.Q_FCU = pattern[4]

        # Station specific
        self.T = route.station_visits
        self.Q_S = [station.station_cap for station in route.stations]
        self.L_CS = L_CS
        self.L_FS = L_FS
        self.I_IC = [customer_arrivals[i][0] for i in range(len(customer_arrivals))]
        self.I_IF = [customer_arrivals[i][1] for i in range(len(customer_arrivals))]
        self.I_OC = [customer_arrivals[i][2] for i in range(len(customer_arrivals))]

        # Vehicle specific
        self.Q_BV = vehicle.battery_capacity
        self.Q_CV = vehicle.bike_capacity + self.Q_CCL + self.Q_FCL - self.Q_CCU - self.Q_FCU
        self.L_BV = vehicle.current_batteries - self.Q_B
        self.L_CV = vehicle.current_charged_bikes + self.Q_CCL - self.Q_CCU
        self.L_FV = vehicle.current_flat_bikes + self.Q_FCL - self.Q_FCU

        # Base Violations
        self.V = base_violations
        self.V_O = base_violations[0]
        self.R_O = 0
        if self.stations[0] in self.charging_stations:
            self.R_O = self.Q_CCU

        # Weights
        self.W_V = 1
        self.W_R = 1
