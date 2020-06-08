import json
import numpy as np


class Station:

    def __init__(self, latitude=None, longitude=None, charged_load=None, flat_load=None, ideal_state=None,
                 charging=False, depot=False, dockgroup_id=None, next_station_probabilities=None,
                 station_travel_time=None, station_car_travel_time=None, name=None, actual_num_bikes=None,
                 max_capacity=None, demand_per_hour=None, battery_rate=0, alfa=1):
        self.id = dockgroup_id
        self.latitude = latitude
        self.longitude = longitude
        self.station_cap = max_capacity
        self.charging_station = charging
        self.battery_rate = battery_rate
        self.depot = depot
        self.station_init_cap = max_capacity
        self.alfa = alfa

        # The following varies with scenario
        self.incoming_charged_bike_rate = dict()
        self.incoming_flat_bike_rate = dict()
        self.ideal_state = ideal_state
        self.init_charged = charged_load
        self.init_flat = flat_load
        self.current_charged_bikes = charged_load
        self.current_flat_bikes = flat_load

        # UIP-sim
        self.dockgroup_id = dockgroup_id
        self.station_travel_time = station_travel_time
        self.station_car_travel_time = station_car_travel_time
        self.name = name
        self.actual_num_bikes = actual_num_bikes

        # Number of charged bikes requested on average from each station per hour. Dict: {hour(0-23): #bikes}
        self.demand_per_hour = demand_per_hour
        # Dict: {id station: probability (normalized?)} --> Not adjusted for stations not included
        self.next_station_probabilities = next_station_probabilities

        # Violations at station
        self.total_starvations = 0
        self.total_congestions = 0

    def get_candidate_stations(self, station_list, tabu_list=list(), max_candidates=10, max_time=1000):
        closest_stations = list()
        for station in station_list:
            if station.id not in tabu_list:
                st_time = self.get_station_car_travel_time(station.id)
                if len(closest_stations) < max_candidates and st_time < max_time:
                    closest_stations.append([station, st_time])
                else:
                    if len(closest_stations) > 0 and closest_stations[-1][-1] > st_time:
                        closest_stations[-1] = [station, st_time]
            closest_stations = sorted(closest_stations, key=lambda l: l[1])
        return closest_stations

    def change_charged_load(self, charged_bikes):
        self.current_charged_bikes += charged_bikes
        if self.current_charged_bikes + self.current_flat_bikes > self.station_cap:
            self.current_charged_bikes = self.station_cap - self.current_flat_bikes
        if self.current_charged_bikes < 0:
            self.current_charged_bikes = 0

    def change_flat_load(self, flat_bikes):
        self.current_flat_bikes += flat_bikes
        if self.current_charged_bikes + self.current_flat_bikes > self.station_cap:
            self.current_flat_bikes = self.station_cap - self.current_charged_bikes
        if self.current_flat_bikes < 0:
            self.current_flat_bikes = 0

    def available_parking(self):
        return max(0, self.station_cap - self.current_flat_bikes - self.current_charged_bikes)

    def get_closest_station_with_capacity(self, stations, num_bikes):
        closest = self.get_candidate_stations(stations, tabu_list=[self.id], max_candidates=50, max_time=1000)
        for st in closest:
            if st[0].available_parking() >= num_bikes and self.id != st[0].id:
                return st[0]

    def get_subset_prob(self, other_stations):
        next_prob = list()
        for st in other_stations:
            if st == self or st.depot:
                next_prob.append(0)
            else:
                next_prob.append(self.next_station_probabilities[st.id])
        return next_prob/np.sum(next_prob)

    def get_outgoing_customer_rate(self, hour):
        return self.demand_per_hour[hour]*self.alfa

    def get_incoming_charged_rate(self, hour):
        return self.incoming_charged_bike_rate[hour]*self.alfa

    def get_incoming_flat_rate(self, hour):
        return self.incoming_flat_bike_rate[hour]*self.alfa

    def get_criticality_score(self, vehicle, time_horizon, hour, driving_time, w_viol, w_drive, w_dev, w_net,
                              first_station):
        # ------- Time to violation -------
        if vehicle.battery_capacity == 0 and self.depot:
            return -100000
        if self.depot and vehicle.current_batteries < 2:
            return 100000
        time_to_starvation = 10000
        time_to_congestion = 10000
        # Time to congestion
        # Ensure that denominator != 0
        if (self.incoming_flat_bike_rate[hour] + self.incoming_charged_bike_rate[hour] -
                self.demand_per_hour[hour] != 0):
            t_cong = (self.station_cap - self.current_charged_bikes - self.current_flat_bikes)/(
                (self.incoming_flat_bike_rate[hour] + self.incoming_charged_bike_rate[hour] -
                 self.demand_per_hour[hour]) / 60)
            if t_cong > 0:
                time_to_congestion = t_cong
        # Time to starvation
        # Ensure that denominator != 0
        if (self.demand_per_hour[hour] - self.incoming_charged_bike_rate[hour]) != 0:
            t_starv = self.current_charged_bikes / ((self.demand_per_hour[hour]
                        - self.incoming_charged_bike_rate[hour]) / 60)
            if t_starv > 0:
                time_to_starvation = t_starv
        time_to_violation = min(time_to_starvation, time_to_congestion)
        if (vehicle.current_station.current_charged_bikes - vehicle.current_station.get_ideal_state(
                hour)) > 0 and (self.incoming_flat_bike_rate[hour] + self.incoming_charged_bike_rate[hour] -
                 self.demand_per_hour[hour]) > 0 and first_station and self.current_charged_bikes > self.get_ideal_state(hour):
            return -10000
        # ------- Deviation at time horizon  -------
        # Starving station
        if self.demand_per_hour[hour] - self.incoming_charged_bike_rate[hour] > 0:
            charged_at_t = self.current_charged_bikes - (self.demand_per_hour[hour] -
                    self.incoming_charged_bike_rate[hour]) * min(time_horizon, time_to_starvation)
            if self.get_ideal_state(hour) - charged_at_t > 0 and first_station and (vehicle.current_charged_bikes < 2 and (
                    vehicle.current_batteries < 2 or self.current_flat_bikes < 2)):
                return -10000
        # Congesting station
        elif self.demand_per_hour[hour] - self.incoming_charged_bike_rate[hour] < 0:
            charged_at_t = self.current_charged_bikes + (self.incoming_charged_bike_rate[hour]
                    - self.demand_per_hour[hour]) * min(time_horizon, time_to_congestion)
            if self.available_parking() == 0 and first_station and vehicle.available_bike_capacity() < 2:
                return -10000
        else:
            charged_at_t = self.current_charged_bikes
        dev = abs(self.get_ideal_state(hour) - charged_at_t)
        net = abs(self.get_incoming_charged_rate(hour) - self.get_outgoing_customer_rate(hour))
        return - w_viol * time_to_violation - w_drive * driving_time + w_dev * dev + w_net * net

    def get_station_car_travel_time(self, end_st_id):
        return self.station_car_travel_time[end_st_id]

    def get_ideal_state(self, hour):
        return self.ideal_state[hour]
