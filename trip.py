from Simulation.event import Event


class Trip(Event):

    id = 0
    bike_to_driving_factor = 1.3

    def __init__(self, start_st, end_st, start_time, stations, charged=True, num_bikes=1, rebalance="nearest"):
        Event.__init__(self, start_time)
        self.start_station = start_st
        self.end_station = end_st
        self.driving_time = start_st.station_car_travel_time[self.end_station.id]
        self.end_time = self.start_time + self.driving_time * Trip.bike_to_driving_factor
        self.charged = charged
        self.num_bikes = num_bikes
        self.stations = stations

        self.rebalance_strategy = rebalance
        self.left_station = False
        self.is_legal = True
        self.redirect = False

    def arrival_handling(self):
        """
        Will check if trip is done, and add bikes to the end station if it is. Return False if trip is not possible
        to start
        """

        if not self.is_legal:
            return False

        elif self.start_station.current_charged_bikes == 0 and not self.left_station:
            self.start_station.total_starvations += 1
            self.is_legal = False
        elif not self.left_station:
            self.start_station.change_charged_load(-self.num_bikes)
            self.left_station = True

        else:
            if self.num_bikes > self.end_station.available_parking():

                self.end_station.total_congestions += 1
                closest_non_full_station = self.end_station.get_closest_station_with_capacity(self.stations,
                                                                                              self.num_bikes)
                self.end_time += self.end_station.station_car_travel_time[
                                     closest_non_full_station.id] * Trip.bike_to_driving_factor

                self.end_station = closest_non_full_station
                self.redirect = True
            else:
                self.redirect = False
                if self.charged or self.end_station.charging_station:
                    self.end_station.change_charged_load(self.num_bikes)
                else:
                    self.end_station.change_flat_load(self.num_bikes)
