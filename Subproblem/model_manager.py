from Subproblem.generate_route_pattern import GenerateRoutePattern
from Subproblem.parameters_subproblem import ParameterSub
from Subproblem.subproblem_model import run_model


class ModelManager:

    time_horizon = 25

    def __init__(self, start_station, all_stations, scenarios, vehicle):
        self.starting_station = start_station
        self.vehicle = vehicle
        self.gen = GenerateRoutePattern(self.starting_station, all_stations, vehicle)
        self.gen.get_columns()
        self.customer_scenarios = scenarios

    def run_all_subproblems(self):
        for route in self.gen.finished_gen_routes:
            for pattern in self.gen.patterns:
                for customer_scenario in self.customer_scenarios:
                    self.run_one_subproblem(route, pattern, customer_scenario)

    def run_one_subproblem(self, route, pattern, customer_scenario):
        customer_arrivals = ModelManager.arrivals_after_visit(route, customer_scenario)
        L_CS = list()
        L_FS = list()
        base_viol = list()
        for i in range(len(route.stations)):
            st_L_CS, st_L_FS = self.get_base_inventory(route.stations[i], route.station_visits[i], customer_scenario)
            st_viol = ModelManager.get_base_violations(route.stations[i], st_L_CS, st_L_FS, customer_arrivals[i])
            L_CS.append(st_L_CS)
            L_FS.append(st_L_FS)
            base_viol.append(st_viol)
        params = ParameterSub(route, self.vehicle, pattern, customer_arrivals, L_CS, L_FS, base_viol)
        run_model(params)

    """
    Returns number of customer arrivals for incoming charged bikes, incoming flat bikes, outgoing charged bikes 
    from time of visit to time horizon based on scenario
    """
    @staticmethod
    def arrivals_after_visit(route, customer_arrivals):
        arrivals = list()
        for i in range(len(route.stations)):
            arrival_time = route.station_visits[i]
            if arrival_time > ModelManager.time_horizon:
                arrivals.append([0, 0, 0])
            else:
                st_arrivals = list()
                for j in range(len(customer_arrivals)):
                    split_index = len(customer_arrivals) - 1
                    for k in range(len(customer_arrivals[j])):
                        if customer_arrivals[j][k] > arrival_time:
                            split_index = k
                            break
                    counted_arrivals = customer_arrivals[j][split_index:]
                    st_arrivals.append(len(counted_arrivals))
                arrivals.append(st_arrivals)
        return arrivals

    """
    Calculate inventory levels at station at time of visit for given customer arrival scenario
    """
    @staticmethod
    def get_base_inventory(station, visit_time_float, customer_arrivals=None):
        visit_time = int(visit_time_float)
        L_CS = station.current_charged_bikes
        L_FS = station.current_flat_bikes
        incoming_charged_bike_times = customer_arrivals[0]
        incoming_flat_bike_times = customer_arrivals[1]
        outgoing_charged_bike_times = customer_arrivals[2]
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
        starvation = abs(min(0, visit_inventory_charged + incoming_charged_bikes - outgoing_charged_bikes))
        congestion = max(0, visit_inventory_charged + visit_inventory_flat + incoming_charged_bikes
                         + incoming_flat_bikes - min(visit_inventory_charged + incoming_charged_bikes,
                                                     outgoing_charged_bikes) - station.station_cap)
        return starvation + congestion
