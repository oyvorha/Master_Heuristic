import datetime
from Station import Station
from google.cloud import bigquery as bq


def setup_stations_students(client):
    """
    function used to setup stations for students without access to all BQ data
    """

    demand_query = "SELECT * FROM `uip-students.loaded_data.simulation_demand_prediction`"
    snapshot_query = "SELECT * FROM `uip-students.loaded_data.simulation_dockgroup_snapshots`"
    dockgroup_movement_query = "SELECT * FROM `uip-students.loaded_data.simulation_station_movement_info`"
    driving_time_query = "SELECT * FROM `uip-students.loaded_data.simulation_driving_times`"

    demand_df = get_data_from_bq(demand_query, client)
    snapshot_df = get_data_from_bq(snapshot_query, client)
    movement_df = get_data_from_bq(dockgroup_movement_query, client)
    car_movement_df = get_data_from_bq(driving_time_query, client)

    datestring = "2019-09-17"
    snapshot_input = get_input_data_from_snapshot_df(snapshot_df, datestring)
    movement_input = get_input_data_from_movement_df(movement_df, datestring, snapshot_keys = snapshot_input.keys())
    demand_input = get_input_data_from_demand_df(demand_df, snapshot_keys = snapshot_input.keys())
    car_movement_input = get_input_data_from_car_movement_df(car_movement_df,
            snapshot_keys = snapshot_input.keys())

    # search for missing station_ids and add them to movement_input
    snap_keys = list(snapshot_input.keys())
    car_missing = set(snap_keys).difference(set(car_movement_input.keys()))

    for missing_station_id in car_missing:
        car_movement_input[missing_station_id] = {id: 3*time for id, time in movement_input[missing_station_id]["avg_trip_duration"].items()}

    stations = []
    for station_id in snapshot_input.keys():
            dockgroup_id = station_id
            next_station_probabilities = movement_input[station_id]["movement_probabilities"]
            station_travel_time = movement_input[station_id]["avg_trip_duration"]
            name = snapshot_input[station_id]["dock_group_title"]
            max_capacity = snapshot_input[station_id]["max_capacity"]
            demand_per_hour = demand_input[station_id] if station_id in demand_input else {i: 0 for i in range(6, 24)}
            actual_num_bikes = snapshot_input[station_id]["num_bikes_list"]

            try:
                station_car_travel_time = car_movement_input[station_id]
            except:
                station_car_travel_time = {station: float(time)*3 for station, time in movement_input[station_id]["avg_trip_duration"].items()}


            s = Station(
                dockgroup_id = dockgroup_id,
                next_station_probabilities = next_station_probabilities,
                station_travel_time =  station_travel_time,
                station_car_travel_time = station_car_travel_time,
                name = name,
                actual_num_bikes = actual_num_bikes,
                max_capacity = max_capacity,
                demand_per_hour =  demand_per_hour,
                )

            stations.append(s)

    return stations


def get_dockgroup_snapshot_input(datestring, client):
    max_capacity, init_num_bikes = get_dockgroup_snapshot_df(datestring, client)

    data = dict()

    id_to_station_name = dict(zip(max_capacity.dock_group_id,
        max_capacity.dock_group_title))

    id_to_max_capacity = dict(zip(max_capacity.dock_group_id,
        max_capacity.total_num_docks))

    id_to_initial_num_bikes = dict(zip(init_num_bikes.dock_group_id,
        init_num_bikes.current_num_bikes))

    for id in id_to_station_name.keys():
        data[id] = {
            "dock_group_title": id_to_station_name[id],
            "max_capacity": id_to_max_capacity[id],
            "initial_num_bikes": id_to_initial_num_bikes[id]
            }

    return data


def get_dockgroup_snapshot_df(datestring, client):
    """
    Need to make a sub query because total_num_docks was not available in 2019,
    so we look up the current number of docks for a given station, and assume that
    this wont have changed
    """

    query = """with stations_at_date as (
            select
             distinct dock_group_id
            from
             `uip-production.bikesharing_NO_oslobysykkel.dockgroup_snapshots`
            where
                date(_partitiontime) = "{}"
        )
        select
          dock_group_id,
          dock_group_title,
          any_value(total_capacity) as total_num_docks
        from
          `uip-production.bikesharing_NO_oslobysykkel.dockgroup_snapshots`
        where
          date(_partitiontime) = current_date()
          and dock_group_id in (select dock_group_id from stations_at_date)
        group by
            dock_group_id, dock_group_title""" .format(datestring)

    max_capacity = get_data_from_bq(query, client)

    #get initial number of bikes
    query = """
        select
          timestamp,
          dock_group_id,
          any_value(available_bikes) as current_num_bikes
        from(
            select rank() over(order by timestamp) as rn,
            timestamp,
            dock_group_id,
            available_bikes
            from
             `uip-production.bikesharing_NO_oslobysykkel.dockgroup_snapshots`
             where extract(date from timestamp) = "{}"
        )
        where
            rn = 1
        group by
            timestamp, dock_group_id
        """ .format(datestring)

    init_num_bikes = get_data_from_bq(query, client)

    return max_capacity, init_num_bikes


def get_input_data_from_movement_df(movement_df, datestring, snapshot_keys):
    """
    Returns a dictionary with data on the form:
    "dock_group_id": {
        "movement_probabilities: {end_dock_id: prob (float)},
        "avg_trip_duration": {end_dock_id: avg_trip_dur_seconds},
        }
    """

    data = dict()
    mf = movement_df
    # remove stations that are not in dockgroup snapshot query
    mf = mf[(mf.start_dock_id.isin(snapshot_keys)) &  (mf.end_dock_id.isin(snapshot_keys))]

    g = mf.groupby("start_dock_id")
    all_dock_ids = [data[0] for data in g]

    for info in g:
        id = info[0]
        df = info[1].copy()

        total_trips = df.num_trips.sum()
        df["move_probability"] = df.num_trips/total_trips

        move_prob = dict(zip(df.end_dock_id, df.move_probability))
        avg_trip_duration = dict(zip(df.end_dock_id, df.avg_duration_in_seconds))

        # add 0s for stations that havent been visited
        for dock_id in all_dock_ids:
            if dock_id not in move_prob:
                move_prob[dock_id] = 0
                avg_trip_duration[dock_id] = 60*60

        dock_info = dict()
        dock_info["movement_probabilities"] = move_prob
        dock_info["avg_trip_duration"] = avg_trip_duration

        data[id] = dock_info

    return data


def get_input_data_from_snapshot_df(df, datestring):
    """
    Returns a dictionary with data on the form:
    "dock_group_id": {
        "num_bikes_list": {datetime: num_bikes (int)},
        "max_capacity": num_docks (int),
        "dock_group_title": string,
        }
    """
    date = datetime.datetime.strptime(datestring, "%Y-%m-%d")

    # df = df[["hour", "minute", "current_num_bikes", "dock_group_id"]]
    df["date"] = df.apply(lambda row:
        date + datetime.timedelta(minutes = row.minute, hours = row.hour), axis = 1)

    data = dict()
    g = df.groupby("dock_group_id")["date", "current_num_bikes"]
    for dock_id in g:
        id = dock_id[0]
        df = dock_id[1]

        dock_info = dict()
        dock_info["num_bikes_list"] = dict(zip(df.date, df.current_num_bikes))
        dock_info["max_capacity"] = df.total_num_docks.mean()
        dock_info["dock_group_title"] = df.iloc[0].dock_group_title

        data[id] = dock_info

    return data


def get_input_data_from_demand_df(demand_df, snapshot_keys):
    # snapshot_keys = [float(val) for val in snapshot_keys]
    data = dict()

    demand_df = demand_df[demand_df["station_id"].isin(snapshot_keys)]
    for station_id, df in demand_df.groupby("station_id"):
        station_data = dict(zip(df.hour, df.bike_demand_per_hour))

        data[station_id] = station_data

    return data


def get_input_data_from_car_movement_df(car_movement_df, snapshot_keys):
    car_movement_df = car_movement_df[car_movement_df.isin(snapshot_keys)]
    data = dict()

    for station_id, df in car_movement_df.groupby("start_station_id"):
        station_data = dict(zip(df.end_station_id, df.driving_time*60)) #to sec
        data[station_id] = station_data

    return data


def get_data_from_bq(query, client):
    dataframe = client.query(query).to_dataframe()
    return dataframe


def get_dockgroup_movement_frame(datestring, client, num_days_back = 30):
    query = get_dockgroup_movement_query(datestring, num_days_back)
    df = get_data_from_bq(query, client)

    return df


def get_demand_frame(datestring, client):
    query = get_demand_query(datestring)
    df = get_data_from_bq(query, client)

    return df


def get_demand_query(datestring):
    # datestring-format: "YYYY-mm-dd"
    query_string = """
    SELECT
      nanmedian_demand_bikes as bike_demand_per_hour,
      dock_group_id as station_id,
      extract(hour from time(timestamp_add(timestamp(valid_date) , interval hour_utc hour), "Europe/Oslo")) as hour
    FROM `urbansharing-data.predictions.optimal_state`
    WHERE valid_date = "{}" and system_id = "oslobysykkel"
    """.format(datestring)

    return query_string


def get_dockgroup_movement_query(datestring, num_days_back = 30):
    """
    Returns a query that calculates the mean trip duration between all combinations of dock groups
    for a given number of previous days.
    """

    query_string = """
    select
      trip_started_dock_group_id as start_dock_id,
      trip_ended_dock_group_id as end_dock_id,
      avg(trip_duration) as avg_duration_in_seconds,
      count(*) as num_trips
    from
      `uip-production.bikesharing_NO_oslobysykkel.trips`
    where
      extract(date from trip_started) < "{0}"
      and extract(date from trip_started) > DATE_SUB("{0}", INTERVAL {1} DAY)
    group by
      start_dock_id, end_dock_id
    """.format(datestring, num_days_back)

    return query_string


if __name__ == '__main__':
    client = bq.Client('uip-students')
    valid_date = "2019-10-10"
    start_time = valid_date + " 06:00:00"
    system_name = "oslobysykkel"
    stations = setup_stations_students(client)
    for st in stations:
        print(st.dockgroup_id)
        print(st.next_station_probabilities)
        print(st.station_travel_time)
        print(st.station_car_travel_time)
        print(st.name)
        print(st.actual_num_bikes)
        print(st.max_capacity)
        print(st.demand_per_hour)
