import numpy as np
from Input.preprocess import get_index


class MasterParameters:

    def __init__(self, route_pattern, subproblem_scores, customer_scenarios, station_objects):

        self.route_pattern = route_pattern
        self.station_objects = station_objects

        # sets
        self.stations = [i for i in range(len(station_objects))]
        self.vehicles = [i for i in range(len(self.route_pattern))]
        self.routes = [[i for i in range(len(gen.finished_gen_routes))] for gen in self.route_pattern]
        self.patterns = [[i for i in range(len(gen.patterns))] for gen in self.route_pattern]
        self.scenarios = [i for i in range(len(customer_scenarios))]

        self.origin_matrix = list()
        self.create_A_matrix()
        self.subproblem_objectives = subproblem_scores
        self.scenario_probabilities = [1/len(customer_scenarios) for i in range(len(customer_scenarios))]

        # single_pattern = Q_B, Q_CCL, Q_CCU, Q_FCL, Q_FCU
        self.pattern_b = list()
        self.pattern_ccl = list()
        self.pattern_ccu = list()
        self.pattern_fcl = list()
        self.pattern_fcu = list()
        self.set_pattern()

        self.vehicle_bike_caps = [gen.vehicle.bike_capacity for gen in self.route_pattern]
        self.station_caps = [station.station_cap for station in station_objects]
        self.init_charged_bike_load = [gen.vehicle.current_charged_bikes for gen in self.route_pattern]
        self.init_flat_bike_load = [gen.vehicle.current_flat_bikes for gen in self.route_pattern]

        self.init_charged_station_load = [station.current_charged_bikes for station in station_objects]
        self.init_flat_station_load = [station.current_flat_bikes for station in station_objects]

    """
    Create pattern variables with shape (v, r, p)
    """
    def set_pattern(self):
        for gen in self.route_pattern:
            v_pattern_b = list()
            v_pattern_ccl = list()
            v_pattern_ccu = list()
            v_pattern_fcl = list()
            v_pattern_fcu = list()
            for r in range(len(gen.finished_gen_routes)):
                v_pattern_b.append([i[0] for i in gen.patterns])
                v_pattern_ccl.append([i[1] for i in gen.patterns])
                v_pattern_ccu.append([i[2] for i in gen.patterns])
                v_pattern_fcl.append([i[3] for i in gen.patterns])
                v_pattern_fcu.append([i[4] for i in gen.patterns])
            self.pattern_b.append(v_pattern_b)
            self.pattern_ccl.append(v_pattern_ccl)
            self.pattern_ccu.append(v_pattern_ccu)
            self.pattern_fcl.append(v_pattern_fcl)
            self.pattern_fcu.append(v_pattern_fcu)

    """
    Create A-matrix with shape (v, r, i)
    """
    def create_A_matrix(self):
        for gen in self.route_pattern:
            v_row = list()
            for route in gen.finished_gen_routes:
                next_station = route.stations[1]
                index = get_index(next_station.id, self.station_objects)
                i_array = np.zeros(len(self.station_objects))
                i_array[index] = 1
                v_row.append(i_array)
            self.origin_matrix.append(v_row)
