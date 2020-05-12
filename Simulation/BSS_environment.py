from Input.preprocess import generate_all_stations, reset_stations
from vehicle import Vehicle
import json
import random
from Output.save_to_excel import save_time_output
import numpy as np
from trip import Trip
from Simulation.event import VehicleEvent
import copy


class Environment:

    charged_rate = 0.95

    def __init__(self, start_hour, simulation_time, stations, vehicles, init_branching, scenarios, memory_mode=False,
                 trigger_start_stack=list(), greedy=False):
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
        self.event_times = list()

        self.memory_mode = memory_mode
        self.initial_stack = None

        self.total_gen_trips = len(trigger_start_stack)
        self.set_up_system()

        self.total_starvations = 0
        self.total_congestions = 0

        self.vehicle_vis = {v.id: [[v.current_station.id], [], [], []] for v in self.vehicles}
        self.print_number_of_bikes()
        while self.current_time < self.simulation_stop:
            self.event_trigger()
        self.print_number_of_bikes()
        self.status()
        self.visualize_system()

    def set_up_system(self):
        for veh1 in self.vehicles:
            veh1.current_station = self.stations[veh1.id]
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

    def generate_trips(self, no_of_hours):
        total_start_stack = self.trigger_start_stack
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
        self.initial_stack = [copy.copy(trip) for trip in self.trigger_start_stack]
        self.total_gen_trips += len(self.trigger_start_stack)

    def visualize_system(self):
        json_stations = {}
        for station in self.stations:
            # [lat, long], charged bikes, flat bikes, starvation score, congestion score
            json_stations[station.id] = [[station.latitude, station.longitude], station.current_charged_bikes,
                                         station.current_flat_bikes, int(station.charging_station), int(station.depot) * 5]
        with open('../Visualization/station_vis.json', 'w') as fp:
            json.dump(json_stations, fp)
        with open('../Visualization/vehicle.json', 'w') as f:
            json.dump(self.vehicle_vis, f)

    def status(self):
        for st in self.stations:
            self.total_congestions += st.total_congestions
            self.total_starvations += st.total_starvations
        print("--------------------- SIMULATION STATUS -----------------------")
        print("Simulation time =", self.simulation_time, "minutes")
        print("Total requested trips =", self.total_gen_trips)
        print("Starvations =", self.total_starvations)
        print("Congestions =", self.total_congestions)

    def print_number_of_bikes(self):
        total_charged = 0
        total_flat = 0
        for station in self.stations:
            total_charged += station.current_charged_bikes
            total_flat += station.current_flat_bikes
        print("Total charged: ", total_charged)
        print("Total flat: ", total_flat)


def run_solution_time_analysis():
    for scenarios in [20, 30, 40, 50]:
        for vehicles in [1, 2, 3, 4, 5]:
            veh = list()
            for i in range(vehicles):
                veh.append(Vehicle(init_battery_load=10, init_charged_bikes=10, init_flat_bikes=10, current_station=None, id=i))
            for branching in [1, 2, 3, 4, 5, 6]:
                for stations in [10, 30, 50, 70]:
                    env = Environment(0, stations, veh, branching, scenarios)
                    # save_time_output(stations, branching, scenarios, vehicles, env.event_times)
                    print("OUTPUT SAVED: ", scenarios, vehicles, branching, stations)


if __name__ == '__main__':
    # run_solution_time_analysis()
    # Single run
    start_hour = 7
    no_stations = 15
    branching = 2
    scenarios = 1
    simulation_time = 60
    stations = generate_all_stations(start_hour)[:no_stations]
    veh = [Vehicle(init_battery_load=10, init_charged_bikes=10, init_flat_bikes=10, current_station=None, id=0)]
    # veh2 = [Vehicle(init_battery_load=10, init_charged_bikes=10, init_flat_bikes=10, current_station=None, id=0)]
    env_base = Environment(start_hour, simulation_time, stations, list(), branching, scenarios)
    stack_base = [copy.copy(trip) for trip in env_base.initial_stack]
    """
    reset_stations(stations, start_hour)
    env3 = Environment(start_hour, simulation_time, stations, veh2, branching, scenarios,
                       trigger_start_stack=env_base.initial_stack, memory_mode=True,
                       greedy=True)
    """
    reset_stations(stations, start_hour)
    env = Environment(start_hour, simulation_time, stations, veh, branching, scenarios, trigger_start_stack=stack_base,
                      memory_mode=True, greedy=False)
