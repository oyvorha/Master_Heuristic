import json
from Station import Station
from vehicle import Vehicle
import copy


def generate_all_stations(scenario):
    with open("Input/station.json", 'r') as f:
        stations = json.load(f)

    station_objects = []
    for id, station in stations.items():
        latitude = float(station[0])
        longitude = float(station[1])
        init_battery_load = station[2][scenario][0]
        init_flat_load = station[2][scenario][1]
        incoming_battery_rate = station[2][scenario][2]
        incoming_flat_rate = station[2][scenario][3]
        outgoing_rate = station[2][scenario][4]
        demand = station[2][scenario][5]
        ideal_state = 10
        obj = Station(latitude, longitude, init_battery_load, init_flat_load
                      , incoming_battery_rate, incoming_flat_rate, outgoing_rate,
                      demand, ideal_state, id)
        station_objects.append(obj)
    return station_objects


def get_station_from_id(id, stations):
    for station in stations:
        if station.id == id:
            return station


class Column:

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
        self.station_visits.append(self.length + added_station_time)

    def generate_extreme_pattern(self, policy='greedy'):
        swap, bat_load, bat_unload, flat_load, flat_unload = (0, 0, 0, 0, 0)
        if policy == 'greedy':
            bat_load = min(self.starting_station.current_battery_bikes, self.vehicle.available_capacity())
            bat_unload = min(self.vehicle.current_battery_bikes, self.starting_station.available_parking())
            flat_load = min(self.starting_station.current_flat_bikes, self.vehicle.available_capacity())
            flat_unload = min(self.vehicle.current_flat_bikes, self.starting_station.available_parking())
            swap = self.starting_station.current_flat_bikes + self.vehicle.current_flat_bikes
        self.upper_extremes = [swap, bat_load, bat_unload, flat_load, flat_unload]


class GenerateColumns:

    flexibility = 7
    branching = 2
    average_handling_time = 3

    def __init__(self, starting_st, stations):
        self.starting_station = get_station_from_id(starting_st, self.all_stations)
        self.time_horizon = 25
        self.vehicle = Vehicle(5, 5, 5)
        self.finished_cols = None
        self.patterns = None
        self.all_stations = stations

    def get_columns(self):
        finished_routes = list()
        construction_routes = [Column(self.starting_station, self.vehicle)]
        while construction_routes:
            for col in construction_routes:
                if col.length < (self.time_horizon - GenerateColumns.flexibility):
                    candidates = col.starting_station.get_candidate_stations(
                        self.all_stations, tabu_list=[c.id for c in col.stations], max_candidates=3)
                    # SORT CANDIDATES BASED ON CRITICALITY HERE?
                    for j in range(GenerateColumns.branching):
                        new_col = copy.deepcopy(col)
                        if len(new_col.stations) == 1:
                            new_col.add_station(candidates[j][0], candidates[j][1])
                        else:
                            new_col.add_station(candidates[j][0], candidates[j][1] + GenerateColumns.average_handling_time)
                        construction_routes.append(new_col)
                else:
                    col.generate_extreme_pattern()
                    finished_routes.append(col)
                construction_routes.remove(col)
        self.finished_cols = finished_routes
        self.gen_patterns()

    def gen_patterns(self):
        rep_col = self.finished_cols[0]
        pat = list()
        for swap in [0, rep_col.upper_extremes[0]]:
            for bat_load in [0, rep_col.upper_extremes[1]]:
                for bat_unload in [0, rep_col.upper_extremes[2]]:
                    for flat_load in [0, rep_col.upper_extremes[3]]:
                        for flat_unload in [0, rep_col.upper_extremes[4]]:
                            pat.append([swap, bat_load, bat_unload, flat_load, flat_unload])
        self.patterns = list(set(tuple(val) for val in pat))
