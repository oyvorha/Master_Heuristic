import copy


class Route:

    def __init__(self, starting_st, vehicle, time_hor=25):
        self.starting_station = starting_st
        self.stations = [starting_st]
        self.length = 0
        self.station_visits = [0]
        self.upper_extremes = None
        self.time_horizon = time_hor
        self.vehicle = vehicle
        self.handling_time = 0.5

    def add_station(self, station, added_station_time):
        self.stations.append(station)
        self.length += added_station_time
        self.station_visits.append(self.length)

    def generate_extreme_decisions(self, policy='greedy'):
        swap, bat_load, flat_load, bat_unload, flat_unload = (0, 0, 0, 0, 0)
        if policy == 'greedy':
            bat_load = min(self.starting_station.current_charged_bikes, self.vehicle.available_bike_capacity())
            bat_unload = min(self.vehicle.current_charged_bikes, self.starting_station.available_parking())
            flat_load = min(self.starting_station.current_flat_bikes, self.vehicle.available_bike_capacity())
            flat_unload = min(self.vehicle.current_flat_bikes, self.starting_station.available_parking())
            swap = min(self.vehicle.current_batteries,
                       self.starting_station.current_flat_bikes + self.vehicle.current_flat_bikes)
        # Q_B, Q_CCL, Q_FCL, Q_CCU, Q_FCU
        self.upper_extremes = [swap, bat_load, flat_load, bat_unload, flat_unload]


class GenerateRoutePattern:

    flexibility = 7
    init_branching = 3
    average_handling_time = 3

    def __init__(self, starting_st, stations, vehicle):
        self.starting_station = starting_st
        self.time_horizon = 25
        self.vehicle = vehicle
        self.finished_gen_routes = None
        self.patterns = None
        self.all_stations = stations

    def get_columns(self):
        finished_routes = list()
        construction_routes = [Route(self.starting_station, self.vehicle)]
        branch = GenerateRoutePattern.init_branching
        while construction_routes:
            for col in construction_routes:
                if col.length < (self.time_horizon - GenerateRoutePattern.flexibility):
                    candidates = col.starting_station.get_candidate_stations(
                        self.all_stations, tabu_list=[c.id for c in col.stations], max_candidates=3)
                    # SORT CANDIDATES BASED ON CRITICALITY HERE?
                    for j in range(branch):
                        new_col = copy.deepcopy(col)
                        if len(new_col.stations) == 1:
                            new_col.add_station(candidates[j][0], candidates[j][1])
                        else:
                            new_col.add_station(candidates[j][0], candidates[j][1] +
                                                GenerateRoutePattern.average_handling_time)
                        construction_routes.append(new_col)
                else:
                    col.generate_extreme_decisions()
                    finished_routes.append(col)
                construction_routes.remove(col)
                if branch > 1:
                    branch -= 1
        self.finished_gen_routes = finished_routes
        self.gen_patterns()

    def gen_patterns(self):
        rep_col = self.finished_gen_routes[0]
        pat = list()
        # Q_B, Q_CCL, Q_FCL, Q_CCU, Q_FCU
        for swap in [0, rep_col.upper_extremes[0]]:
            for bat_load in [0, rep_col.upper_extremes[1]]:
                for flat_load in [0, rep_col.upper_extremes[2]]:
                    for bat_unload in [0, rep_col.upper_extremes[3]]:
                        for flat_unload in [0, rep_col.upper_extremes[4]]:
                            pat.append([swap, bat_load, flat_load, bat_unload, flat_unload])
        self.patterns = list(set(tuple(val) for val in pat))
