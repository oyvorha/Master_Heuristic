from generate_route_pattern import generate_all_stations, GenerateRoutePattern
from parameters_subproblem import ParameterSub
from vehicle import Vehicle
from subproblem_model import run_model
import numpy as np


class ModelManager:

    stations = generate_all_stations('A')[:30]
    time_horizon = 25

    def __init__(self, start_station_id, vehicle=Vehicle(5, 5, 5)):
        self.starting_station = ModelManager.stations[ModelManager.get_index(start_station_id)]
        self.vehicle = vehicle
        self.gen = GenerateRoutePattern(self.starting_station, ModelManager.stations, vehicle)
        self.gen.get_columns()

    def run_all_subproblems(self):
        for route in self.gen.finished_gen_routes:
            for pattern in self.gen.patterns:
                self.run_one_subproblem(route, pattern)

    def run_one_subproblem(self, route, pattern):
        customer_arrivals = ModelManager.poisson_draw(route)
        L_CS = list()
        L_FS = list()
        base_viol = list()
        for i in range(len(route.stations)):
            st_L_CS, st_L_FS = self.get_base_inventory(route.stations[i], route.station_visits[i])
            st_viol = ModelManager.get_base_violations(route.stations[i], st_L_CS, st_L_FS, customer_arrivals[i])
            L_CS.append(st_L_CS)
            L_FS.append(st_L_FS)
            base_viol.append(st_viol)
        params = ParameterSub(route.stations, self.vehicle, pattern, customer_arrivals, L_CS, L_FS, base_viol)
        run_model(params)

    @staticmethod
    def get_index(station_id):
        for i in range(len(ModelManager.stations)):
            if ModelManager.stations[i].id == station_id:
                return i

    """
    Returns Poisson draw for incoming charged bikes, incoming flat bikes, outgoing charged bikes from time of visit 
    to time horizon
    """
    @staticmethod
    def poisson_draw(route):
        arrivals = list()
        for i in range(len(route.stations)):
            if route.station_visits[i] > ModelManager.time_horizon:
                arrivals.append([0, 0, 0])
            else:
                st_arrivals = list()
                st_arrivals.append(np.random.poisson(route.stations[i].incoming_charged_bike_rate *
                                                     (ModelManager.time_horizon - route.station_visits[i])))
                st_arrivals.append(np.random.poisson(route.stations[i].incoming_flat_bike_rate *
                                                     (ModelManager.time_horizon - route.station_visits[i])))
                st_arrivals.append(np.random.poisson(route.stations[i].outgoing_charged_bike_rate *
                                                     (ModelManager.time_horizon - route.station_visits[i])))
                arrivals.append(st_arrivals)
        return arrivals

    @staticmethod
    def poisson_simulation(intensity_rate, time_steps):
        times = list()
        for t in range(time_steps):
            arrival = np.random.poisson(intensity_rate * time_steps)
            for i in range(arrival):
                times.append(t)
        return times

    @staticmethod
    def get_base_inventory(station, visit_time_float, test_mode=None):
        visit_time = int(visit_time_float)
        L_CS = station.current_battery_bikes
        L_FS = station.current_flat_bikes
        if test_mode:
            incoming_charged_bike_times = test_mode[0]
            incoming_flat_bike_times = test_mode[1]
            outgoing_charged_bike_times = test_mode[2]
        else:
            incoming_charged_bike_times = ModelManager.poisson_simulation(station.incoming_charged_bike_rate, visit_time)
            incoming_flat_bike_times = ModelManager.poisson_simulation(station.incoming_charged_bike_rate, visit_time)
            outgoing_charged_bike_times = ModelManager.poisson_simulation(station.outgoing_charged_bike_rate, visit_time)
        for i in range(visit_time):
            c1 = incoming_charged_bike_times.count(i)
            c2 = incoming_flat_bike_times.count(i)
            c3 = outgoing_charged_bike_times.count(i)
            L_CS = max(0, min(station.station_cap - L_FS, L_CS + c1 - c3))
            L_FS = min(station.station_cap - L_CS, L_FS + c2)
        return L_CS, L_FS

    """
    Returning base violations from time of visit to time horizon. Assuming optimal sequencing of customer arrivals
    """
    @staticmethod
    def get_base_violations(station, visit_inventory_charged, visit_inventory_flat, customer_arrivals):
        incoming_charged_bikes = customer_arrivals[0]
        incoming_flat_bikes = customer_arrivals[1]
        outgoing_charged_bikes = customer_arrivals[2]
        starvation = max(0, visit_inventory_charged + incoming_charged_bikes - outgoing_charged_bikes)
        congestion = max(0, visit_inventory_charged + visit_inventory_flat + incoming_charged_bikes
                         + incoming_flat_bikes - outgoing_charged_bikes - station.station_cap)
        return starvation + congestion


manager = ModelManager('378')
manager.run_one_subproblem(manager.gen.finished_gen_routes[0], manager.gen.patterns[0])
