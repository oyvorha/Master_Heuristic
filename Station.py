import json


class Station:

        def __init__(self, latitude, longitude, charged_load, flat_load, incoming_charged_bike_rate, incoming_flat_bike_rate,
                     outgoing_charged_bike_rate, ideal_state, station_id, station_cap=20, charging=False):
            self.id = station_id
            self.latitude = latitude
            self.longitude = longitude
            self.station_cap = station_cap
            self.charging_station = charging

            # The following varies with scenario
            self.init_station_load = charged_load
            self.init_flat_station_load = flat_load
            self.incoming_charged_bike_rate = incoming_charged_bike_rate
            self.incoming_flat_bike_rate = incoming_flat_bike_rate
            self.outgoing_charged_bike_rate = outgoing_charged_bike_rate
            self.ideal_state = ideal_state
            self.current_charged_bikes = charged_load
            self.current_flat_bikes = flat_load

        def get_candidate_stations(self, station_list, tabu_list=None, max_candidates=7, max_time=25):
            closest_stations = list()
            for station in station_list:
                if station.id not in tabu_list:
                    id_key = str(self.id) + '_' + str(station.id)
                    with open("../Input/times.json", 'r') as f:
                        time_json = json.load(f)
                        st_time = time_json[id_key][0]
                        if len(closest_stations) < max_candidates and st_time < max_time:
                            closest_stations.append([station, st_time])
                        else:
                            if closest_stations[-1][-1] > st_time:
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
            return max(0, self.station_cap - self.current_flat_bikes + self.current_charged_bikes)
