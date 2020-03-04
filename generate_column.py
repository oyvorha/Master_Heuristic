import json
from Station import Station


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


stations = generate_all_stations('A')


def get_station_from_id(id):
    for station in stations:
        if station.id == id:
            return station


class Column:

    def __init__(self, starting_st, vehicle, time_hor=25):
        self.stations = [starting_st]
        self.length = 0
        self.station_visits = [0]
        self.activity = list()
        self.violations = 0
        self.deviations = 0
        self.congestion = 0
        self.reward = 0
        self.time_horizon = time_hor
        self.vehicle = vehicle

    def add_station(self, station, added_station_time):
        self.stations.append(station)
        self.length += added_station_time
        self.station_visits.append(self.length + added_station_time)

    def optimize_activity(self, handling_time=0.5, policy='greedy'):
        swap, bat_load, bat_unload, flat_load, flat_unload = (0, 0, 0, 0, 0)
        if policy == 'greedy':
            for i in range(len(self.stations)):
                time_of_visit = self.station_visits[i]
                station = self.stations[i]
                if station.init_flat_station_load + time_of_visit*station.flat_rate > 0:
                    if self.vehicle.current_batteries > (station.init_flat_station_load + time_of_visit*station.flat_rate):
                        swap = int(station.init_flat_station_load + time_of_visit*station.flat_rate)
                    else:
                        swap = self.vehicle.current_batteries
                    self.vehicle.swap_batteries(swap)
                    station.change_battery_load(swap + time_of_visit*station.battery_rate)
                    station.change_flat_load(-swap + time_of_visit*station.flat_rate)
                if station.outgoing_rate > 0:
                    bat_unload = min(self.vehicle.current_battery_bikes, station.available_parking())
                    self.vehicle.change_battery_bikes(-bat_unload)
                    flat_load = min(self.vehicle.available_capacity(), station.current_flat_bikes)
                    if bat_unload == station.available_parking():
                        station.change_flat_load(flat_load)
                        bat_unload += station.available_parking()
                        self.vehicle.change_battery_bikes(-station.available_parking())
                    self.vehicle.change_flat_bikes(flat_load)
                if station.outgoing_rate < 0:
                    bat_load = min(station.current_battery_bikes, self.vehicle.available_capacity())
                    self.vehicle.change_battery_bikes(bat_load)
                    flat_unload = min(self.vehicle.current_flat_bikes, station.available_parking())
                    if bat_load == self.vehicle.available_capacity():
                        self.vehicle.change_battery_bikes(-flat_unload)
                        bat_load += self.vehicle.available_capacity()
                        self.vehicle.change_battery_bikes(self.vehicle.available_capacity())
                self.activity.append((swap, bat_load, bat_unload, flat_load, flat_unload))
                added_time = (swap + bat_load + bat_unload + flat_load + flat_unload) * handling_time
                for t in self.station_visits[i:]:
                    t + added_time

    def calculate_violations(self):
        total_violation = 0
        for i in range(len(self.stations)):
            time_of_visit = self.station_visits[i]
            station = self.stations[i]
            swap, bat_load, bat_unload, flat_load, flat_unload = self.activity[i]
            if time_of_visit < self.time_horizon:
                if station.init_station_load - time_of_visit*station.outgoing_rate < 0:
                    total_violation += time_of_visit*station.outgoing_rate - station.init_station_load
                if (station.init_station_load + station.init_flat_station_load
                    - time_of_visit*station.outgoing_rate) > station.station_cap:
                    total_violation += (station.init_station_load + station.init_flat_station_load +
                                        time_of_visit*station.outgoing_rate - station.station_cap)
                remaining_time = self.time_horizon - time_of_visit
                if station.init_station_load + swap + bat_load - bat_unload - remaining_time*station.outgoing_rate < 0:
                    total_violation += (remaining_time*station.outgoing_rate - station.init_station_load
                                        + swap + bat_load - bat_unload)
                if (station.init_station_load + swap + bat_load - bat_unload + flat_load - flat_unload
                    - remaining_time*station.outgoing_rate) > station.station_cap:
                    total_violation += (remaining_time*station.outgoing_rate - station.init_station_load
                                        + swap + bat_load - bat_unload + flat_load - flat_unload)
            else:
                pass
                # Violations ved besøk etter time horizon
        self.violations = total_violation

    def calculate_deviation_and_congestion(self):
        dev = 0
        congestion = 0
        for i in range(len(self.stations)):
            time_of_visit = self.station_visits[i]
            station = self.stations[i]
            swap, bat_load, bat_unload, flat_load, flat_unload = self.activity[i]
            if time_of_visit < self.time_horizon:
                battery_bikes = max(0, station.init_station_load - time_of_visit * station.outgoing_rate
                                    ) + swap + bat_unload - bat_load - max(0, station.current_battery_bikes - (
                                    self.time_horizon - time_of_visit) * station.outgoing_rate)
                dev += abs(station.ideal_state - battery_bikes)
                if (station.init_station_load + station.init_flat_station_load - station.outgoing_rate * time_of_visit
                        ) > station.station_cap:
                    congestion += station.init_station_load + station.init_flat_station_load - station.outgoing_rate * \
                                  time_of_visit - station.station_cap
                if (station.available_parking() + station.outgoing_rate * (self.time_horizon - time_of_visit)) < 0:
                    congestion += (station.available_parking() + station.outgoing_rate * (self.time_horizon - time_of_visit))
            else:
                if (station.init_station_load + station.init_flat_station_load - station.outgoing_rate * self.time_horizon
                ) > station.station_cap:
                    congestion += station.init_station_load + station.init_flat_station_load - station.outgoing_rate * \
                                  self.time_horizon - station.station_cap
        self.deviations = dev
        self.congestion = congestion

    def calculate_reward(self):
        reward = 0
        for i in range(len(self.station_visits)):
            if self.station_visits[i] > self.time_horizon:
                reward += self.activity[i][0]
        self.reward = reward


class GenerateColumns:

    flexibility = 5

    def __init__(self, starting_st):
        starting_station_id = starting_st
        time_horizon = 25
        branching = 5

    def get_columns(self):
        finished_routes = list()
        construction_routes = []
        while True:
            pass
