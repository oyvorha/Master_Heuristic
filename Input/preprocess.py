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
    valid_date = "2019-10-10"
    start_time = valid_date + " 06:00:00"
    system_name = "oslobysykkel"
    stations_uip = setup_stations_students(client)
    print("UIP DB objects collected")

    with open('../Input/station.json', 'r') as f:
        stations = json.load(f)

    station_obj = list()

    for id_json, station in stations.items():
        for st in stations_uip:
            if st.id == id_json:
                latitude = float(station[0])
                longitude = float(station[1])
                if int(st.id) % 5 == 0:
                    st.battery_rate = 1
                    st.charging_station = True
                else:
                    st.battery_rate = 0.95
                st.latitude = latitude
                st.longitude = longitude
                st.ideal_state = st.station_cap // 2
                st.current_charged_bikes = min(st.station_cap, round(st.battery_rate * st.actual_num_bikes[init_hour], 0))
                st.current_flat_bikes = min(st.station_cap - st.current_charged_bikes, round((1 - st.battery_rate) * st.actual_num_bikes[init_hour], 0))
                station_obj.append(st)
    subset = station_obj[:n]
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
                incoming += stat.demand_per_hour[hour] * stat.next_station_probabilities[st2.id]
            st2.incoming_charged_bike_rate[hour] = incoming * st2.battery_rate
            st2.incoming_flat_bike_rate[hour] = incoming * (1-st2.battery_rate)
    return subset


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
