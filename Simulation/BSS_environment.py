import json
import random
import numpy as np
from trip import Trip
from Simulation.event import VehicleEvent
import copy


class Environment:

    charged_rate = 0.95

    def __init__(self, start_hour, simulation_time, stations, vehicles, init_branching, scenarios, memory_mode=False,
                 trigger_start_stack=list(), greedy=False, weights=(0.5, 0.1, 0.4, 0.75, 0.25)):
        self.stations = stations
        self.vehicles = vehicles
        self.current_time = start_hour * 60
        self.simulation_time = simulation_time
        self.simulation_stop = simulation_time + self.current_time
        self.trigger_start_stack = trigger_start_stack
        self.trigger_stack = list()
        self.init_branching = init_branching
        self.scenarios = scenarios
        self.greedy = greedy
        self.weights = weights
        self.event_times = list()

        self.memory_mode = memory_mode
        self.initial_stack = None

        self.total_gen_trips = len(trigger_start_stack)
        self.set_up_system()

        self.total_starvations = 0
        self.total_congestions = 0

        self.vehicle_vis = {v.id: [[v.current_station.id], [], [], []] for v in self.vehicles}
        self.print_number_of_bikes()

    def run_simulation(self):
        while self.current_time < self.simulation_stop:
            self.event_trigger()
        self.end_simulation()

    def set_up_system(self):
        for veh1 in self.vehicles:
            self.trigger_stack.append(VehicleEvent(self.current_time, self.current_time, veh1, self, greedy=self.greedy))
        if not self.memory_mode:
            self.generate_trips(self.simulation_time // 60)
        self.trigger_stack = self.trigger_start_stack + self.trigger_stack
        self.trigger_stack = sorted(self.trigger_stack, key=lambda l: l.end_time)

    def event_trigger(self):
        if len(self.trigger_start_stack) == 0:
            event = self.trigger_stack.pop(0)
            self.current_time = event.end_time
        elif len(self.trigger_stack) == 0:
            event = self.trigger_start_stack.pop(0)
            self.current_time = event.start_time
        else:
            if self.trigger_start_stack[0].start_time < self.trigger_stack[0].end_time:
                event = self.trigger_start_stack.pop(0)
                self.current_time = event.start_time
            else:
                event = self.trigger_stack.pop(0)
                self.current_time = event.end_time
        event.arrival_handling()
        if event.event_time > 0:
            self.event_times.append(event.event_time)
        if isinstance(event, Trip) and event.redirect:
            self.trigger_stack.append(event)
            self.trigger_stack = sorted(self.trigger_stack, key=lambda l: l.end_time)

    def generate_trips(self, no_of_hours, gen=False):
        if not gen:
            total_start_stack = self.trigger_start_stack
        else:
            total_start_stack = list()
        current_hour = self.current_time // 60
        for hour in range(current_hour, current_hour + no_of_hours):
            trigger_start = list()
            for st in self.stations:
                if not st.depot:
                    num_bikes_leaving = int(np.random.poisson(lam=st.get_outgoing_customer_rate(hour), size=1)[0])
                    next_st_prob = st.get_subset_prob(self.stations)
                    for i in range(num_bikes_leaving):
                        start_time = random.randint(hour * 60, (hour+1) * 60)
                        next_station = np.random.choice(self.stations, p=next_st_prob)
                        charged = np.random.binomial(1, Environment.charged_rate)
                        trip = Trip(st, next_station, start_time, self.stations,
                                    charged=charged, num_bikes=1, rebalance="nearest")
                        trigger_start.append(trip)
            total_start_stack += trigger_start
        self.trigger_start_stack = sorted(total_start_stack, key=lambda l: l.start_time)
        init_stack = [copy.copy(trip) for trip in self.trigger_start_stack]
        self.initial_stack = init_stack
        self.total_gen_trips += len(self.trigger_start_stack)
        return init_stack

    def end_simulation(self):
        for st in self.stations:
            self.total_congestions += st.total_congestions
            self.total_starvations += st.total_starvations
        self.visualize_system()
        self.status()

    def visualize_system(self):
        json_stations = {}
        for station in self.stations:
            # [lat, long], charged bikes, flat bikes, starvation score, congestion score
            json_stations[station.id] = [[station.latitude, station.longitude], station.current_charged_bikes,
                                         station.current_flat_bikes, station.total_congestions, station.total_starvations,
                                         station.station_cap, int(station.depot)]
        with open('Visualization/station_vis.json', 'w') as fp:
            json.dump(json_stations, fp)
        with open('Visualization/vehicle.json', 'w') as f:
            json.dump(self.vehicle_vis, f)

    def status(self):
        print("--------------------- SIMULATION STATUS -----------------------")
        print("Simulation time =", self.simulation_time, "minutes")
        print("Total requested trips =", self.total_gen_trips)
        print("Starvations =", self.total_starvations)
        print("Congestions =", self.total_congestions)
        self.print_number_of_bikes()
        print("---------------------------------------------------------------")

    def print_number_of_bikes(self):
        total_charged = 0
        total_flat = 0
        for station in self.stations:
            total_charged += station.current_charged_bikes
            total_flat += station.current_flat_bikes
        print("Total charged: ", total_charged)
        print("Total flat: ", total_flat)
