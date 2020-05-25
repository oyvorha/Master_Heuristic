import copy
import json


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
        if not self.starting_station.depot:
            if policy == 'greedy':
                # Make ideal state artificially lower for increased flexibility --> Temporarily set to 3
                bat_load = max(0, min(self.starting_station.current_charged_bikes, self.vehicle.available_bike_capacity(),
                                      self.starting_station.current_charged_bikes - self.starting_station.ideal_state - 3))
                bat_unload = max(0, min(self.vehicle.current_charged_bikes, self.starting_station.available_parking(),
                                 self.starting_station.ideal_state - self.starting_station.current_charged_bikes))
                flat_load = min(self.starting_station.current_flat_bikes, self.vehicle.available_bike_capacity())
                flat_unload = min(self.vehicle.current_flat_bikes, self.starting_station.available_parking())
                swap = min(self.vehicle.current_batteries,
                           self.starting_station.current_flat_bikes + self.vehicle.current_flat_bikes)
        # Q_B, Q_CCL, Q_FCL, Q_CCU, Q_FCU
        self.upper_extremes = [swap, bat_load, flat_load, bat_unload, flat_unload]


class GenerateRoutePattern:

    flexibility = 3
    average_handling_time = 6

    # Criticality weights
    w_drive = 0.3
    w_dev = 0.2
    w_viol = 0.5

    def __init__(self, starting_st, stations, vehicle, hour, init_branching=8, simple_candidate=False, dynamic=True):
        self.starting_station = starting_st
        self.time_horizon = 25
        self.vehicle = vehicle
        self.finished_gen_routes = None
        self.patterns = None
        self.all_stations = stations
        self.init_branching = init_branching
        self.hour = hour
        self.simple_candidate = simple_candidate
        self.dynamic = dynamic

    def get_columns(self):
        finished_routes = list()
        construction_routes = [Route(self.starting_station, self.vehicle)]
        while construction_routes:
            for col in construction_routes:
                if col.length < (self.time_horizon - GenerateRoutePattern.flexibility):

                    if self.simple_candidate:
                        cand_scores = col.starting_station.get_candidate_stations(
                            self.all_stations, tabu_list=[c.id for c in col.stations], max_candidates=9)
                    # candidates = all stations
                    else:
                        candidates = self.all_stations
                        cand_scores = list()

                        # Calculate criticality score for all stations
                        for st in candidates:
                            if st not in col.stations:
                                driving_time = col.stations[-1].get_station_car_travel_time(st.id)
                                score = st.get_criticality_score(self.vehicle, self.time_horizon, self.hour,
                                                                 driving_time, self.w_viol,
                                                                 self.w_drive, self.w_dev)
                                cand_scores.append([st, driving_time, score])

                        # Sort candidates by criticality score
                        cand_scores = sorted(cand_scores, key=lambda l: l[2], reverse=True)

                    # Filtering (remember on/off opportunity)

                    # Extend the route with the B best stations
                    for j in range(self.init_branching):
                        new_col = copy.deepcopy(col)
                        new_col.add_station(cand_scores[j][0], cand_scores[j][1] +
                                            GenerateRoutePattern.average_handling_time)
                        construction_routes.append(new_col)

                else:
                    col.generate_extreme_decisions()
                    finished_routes.append(col)
                construction_routes.remove(col)
                if self.init_branching > 1 and self.dynamic:
                    self.init_branching -= 1
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
