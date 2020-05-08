import json
from Station import Station
from google.cloud import bigquery as bq
from Simulation.set_up_simulation import setup_stations_students


def get_driving_time_from_id(station_id_1, station_id_2):
    id_key = str(station_id_1) + '_' + station_id_2
    with open('../Input/times.json', 'r') as f:
        time_json = json.load(f)
    return time_json[id_key]


def generate_all_stations(init_hour):
    client = bq.Client('uip-students')
    valid_date = "2019-10-10"
    start_time = valid_date + " 06:00:00"
    system_name = "oslobysykkel"
    stations_uip = setup_stations_students(client)
    print("UIP DB objects collected")

    with open('../Input/station.json', 'r') as f:
        stations = json.load(f)

    station_objects = []
    for id, station in stations.items():

        battery_rate = 0.5
        flat_rate = 0.5
        charging_station = False

        if int(id) % 5 == 0:
            battery_rate = 1
            flat_rate = 0
            charging_station = True

        latitude = float(station[0])
        longitude = float(station[1])

        for st in stations_uip:
            if st.dockgroup_id == id:
                station_cap = st.station_cap
                demand_per_hour = st.demand_per_hour
                next_station_probabilities = st.next_station_probabilities
                # Nå er antall sykler boostet
                init_charged_load = min(station_cap, round(battery_rate * st.actual_num_bikes[init_hour], 0))
                init_flat_load = min(station_cap - init_charged_load, round(flat_rate * st.actual_num_bikes[init_hour], 0))
                incoming_flat_bike_rate = dict()
                incoming_charged_bike_rate = dict()
                for hour in range(24):
                    try:
                        incoming_flat_bike_rate[hour] = max(0, flat_rate * (st.actual_num_bikes[hour+1] -
                                                                            st.actual_num_bikes[hour])) / 60

                        if battery_rate * st.actual_num_bikes[init_hour+1] != 0:
                            incoming_charged_bike_rate[hour] = max(0, (battery_rate * (st.actual_num_bikes[hour+1]
                                                                                       - st.actual_num_bikes[hour]) +
                                                                       demand_per_hour[hour])) / 60
                        else:
                            incoming_charged_bike_rate[hour] = 0
                    except KeyError:
                        incoming_flat_bike_rate[hour] = incoming_flat_bike_rate[hour-1]
                        incoming_charged_bike_rate[hour] = incoming_charged_bike_rate[hour-1]

                ideal_state = 10
                obj = Station(latitude, longitude, init_charged_load, init_flat_load
                              , incoming_charged_bike_rate, incoming_flat_bike_rate, ideal_state,
                              id, next_station_probabilities=next_station_probabilities, demand_per_hour=demand_per_hour,
                              max_capacity=station_cap, charging=charging_station)
                station_objects.append(obj)
    return station_objects


def reset_stations(stations, init_hour):
    client = bq.Client('uip-students')
    stations_uip = setup_stations_students(client)
    print("UIP DB reset objects collected")

    for station in stations:

        station.total_starvations = 0
        station.total_congestions = 0

        if station.charging_station:
            battery_rate = 1
            flat_rate = 0
        else:
            battery_rate = 0.5
            flat_rate = 0.5

        for st in stations_uip:
            if st.dockgroup_id == station.id:
                station.current_charged_bikes = min(station.station_cap, round(battery_rate * st.actual_num_bikes[init_hour], 0))
                station.current_flat_bikes = min(station.station_cap - station.current_charged_bikes,
                                                 round(flat_rate * st.actual_num_bikes[init_hour], 0))


def get_index(station_id, stations):
    for i in range(len(stations)):
        if stations[i].id == station_id:
            return i
