
class Vehicle:

    def __init__(self, init_battery_load, init_charged_bikes, init_flat_bikes, bike_cap=20, bat_cap=20):
        self.current_batteries = init_battery_load
        self.current_charged_bikes = init_charged_bikes
        self.current_flat_bikes = init_flat_bikes
        self.bike_capacity = bike_cap
        self.battery_capacity = bat_cap

    def change_battery_bikes(self, bikes):
        self.current_charged_bikes += bikes
        if self.current_charged_bikes < 0:
            self.current_charged_bikes = 0
        if self.current_charged_bikes + self.current_flat_bikes > self.bike_capacity:
            self.current_charged_bikes = self.bike_capacity - self.current_flat_bikes

    def change_flat_bikes(self, bikes):
        self.current_flat_bikes += bikes
        if self.current_flat_bikes < 0:
            self.current_flat_bikes = 0
        if self.current_charged_bikes + self.current_flat_bikes > self.bike_capacity:
            self.current_flat_bikes = self.bike_capacity - self.current_charged_bikes

    def swap_batteries(self, batteries):
        self.current_batteries = max(0, self.current_batteries - batteries)

    def available_bike_capacity(self):
        return max(0, self.bike_capacity - (self.current_flat_bikes + self.current_charged_bikes))
