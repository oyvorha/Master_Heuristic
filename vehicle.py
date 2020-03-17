
class Vehicle:

    def __init__(self, init_battery_load, init_battery_bikes, init_flat_bikes, cap=20, bat_cap=20):
        self.current_batteries = init_battery_load
        self.current_battery_bikes = init_battery_bikes
        self.current_flat_bikes = init_flat_bikes
        self.bike_capacity = cap
        self.battery_capacity = bat_cap

    def change_battery_bikes(self, bikes):
        self.current_battery_bikes -= bikes

    def change_flat_bikes(self, bikes):
        self.current_flat_bikes -= bikes

    def swap_batteries(self, batteries):
        self.current_batteries -= batteries

    def available_capacity(self):
        return max(0, self.bike_capacity - (self.current_flat_bikes + self.current_battery_bikes))
