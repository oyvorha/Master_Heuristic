import json
from google.cloud import bigquery as bq
from Simulation.set_up_simulation import setup_stations_students


def get_driving_time_from_id(station_id_1, station_id_2):
    id_key = str(station_id_1) + '_' + station_id_2
    with open('../Input/times.json', 'r') as f:
        time_json = json.load(f)
    return time_json[id_key]


def generate_all_stations(init_hour, n):
    client = bq.Client('uip-students')
    # valid_date = "2019-10-10"
    stations_uip = setup_stations_students(client)
    print("UIP DB objects collected")
    demand_met = 0.75

    with open('Input/station.json', 'r') as f:
        ideal_state_json = json.load(f)

    for st in stations_uip:
        if int(st.id) % 10 == 0:
            st.battery_rate = 1
            st.charging_station = True
        else:
            st.battery_rate = 0.95
        if st.id in ideal_state_json.keys():
            ideal = {int(k): int(v) for k, v in ideal_state_json[st.id].items()}
            st.ideal_state = ideal
        else:
            ideal = {}
            for hour in range(0, 24):
                ideal[hour] = st.station_cap // 2
            st.ideal_state = ideal

        st.current_charged_bikes = min(st.station_cap, st.actual_num_bikes[init_hour])
        st.current_flat_bikes = 0
        st.init_charged = st.current_charged_bikes
        st.init_flat = st.current_flat_bikes

    subset = stations_uip[:n]
    subset_ids = [s.id for s in subset]

    for st1 in subset:
        subset_prob = 0
        for st_id, prob in st1.next_station_probabilities.items():
            if st_id in subset_ids:
                subset_prob += prob
        for hour in range(24):
            st1.demand_per_hour[hour] *= subset_prob
        for s_id in subset_ids:
            st1.next_station_probabilities[s_id] /= subset_prob
    for st2 in subset:
        for hour in range(24):
            incoming = 0
            for stat in subset:
                incoming += stat.demand_per_hour[hour] * demand_met * stat.next_station_probabilities[st2.id]
            st2.incoming_charged_bike_rate[hour] = incoming * st2.battery_rate
            st2.incoming_flat_bike_rate[hour] = incoming * (1-st2.battery_rate)
    return subset


def generate_pattern_stations(n):
    client = bq.Client('uip-students')
    # valid_date = "2019-10-10"
    stations_uip = setup_stations_students(client)
    print("UIP DB objects collected")
    demand_met = 0.5

    for st in stations_uip:
            st.battery_rate = 0.5
            st.ideal_state = st.station_cap // 2
            st.current_charged_bikes = 8
            st.current_flat_bikes = 8
            st.init_charged = st.current_charged_bikes
            st.init_flat = st.current_flat_bikes
            ideal = {}
            for hour in range(0, 24):
                ideal[hour] = 16
            st.ideal_state = ideal
    subset = stations_uip[:n]
    subset_ids = [s.id for s in subset]
    for st1 in subset:
        subset_prob = 0
        for st_id, prob in st1.next_station_probabilities.items():
            if st_id in subset_ids:
                subset_prob += prob
        for hour in range(24):
            st1.demand_per_hour[hour] *= subset_prob
        for s_id in subset_ids:
            st1.next_station_probabilities[s_id] /= subset_prob
    for st2 in subset:
        for hour in range(24):
            incoming = 0
            for stat in subset:
                incoming += stat.demand_per_hour[hour] * demand_met * stat.next_station_probabilities[st2.id]
            st2.incoming_charged_bike_rate[hour] = incoming * st2.battery_rate
            st2.incoming_flat_bike_rate[hour] = incoming * (1-st2.battery_rate)
    return subset


def reset_stations(stations):

    for station in stations:

        station.total_starvations = 0
        station.total_congestions = 0

        station.current_charged_bikes = station.init_charged
        station.current_flat_bikes = station.init_flat


def reset_cap_stations(stations, multiplier):
    reset_stations(stations)
    for st in stations:
        st.station_cap = round(st.station_init_cap * multiplier, 0)


def get_index(station_id, stations):
    for i in range(len(stations)):
        if stations[i].id == station_id:
            return i
