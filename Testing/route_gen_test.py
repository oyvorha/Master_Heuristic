import unittest
from Subproblem.generate_route_pattern import GenerateRoutePattern, Route
from vehicle import Vehicle
from Station import Station
from Input.preprocess import generate_all_stations, get_driving_time_from_id


class RouteGenTester(unittest.TestCase):

    test_stations = generate_all_stations('A')

    test_vehicle = Vehicle(init_battery_load=10, init_charged_bikes=5, init_flat_bikes=5, bike_cap=20, bat_cap=20)

    start_station = Station(longitude=59.9306, latitude=10.714780000000001, charged_load=5, flat_load=2,
                            incoming_charged_bike_rate=0.04, incoming_flat_bike_rate=0.017,
                            outgoing_charged_bike_rate=0.051, ideal_state=10, station_id='386',
                            station_cap=10, charging=False)

    test_route = Route(starting_st=start_station, vehicle=test_vehicle, time_hor=25)

    test_gen_route = GenerateRoutePattern(starting_st=start_station, stations=test_stations, vehicle=test_vehicle)
    test_gen_route.get_columns()

    def test_route_obj(self):
        route = RouteGenTester.test_route
        for i in [3, 5, 9]:
            next_station = RouteGenTester.test_stations[i]
            added_time = get_driving_time_from_id(route.stations[0].id, next_station.id)[0]
            route.add_station(next_station, added_time)
        self.assertEqual(route.station_visits, [0, 13.18, 21.0, 30.25])


    """
    Temporary testing
    """
    def test_extreme_pattern(self):
        # swap, bat_load, bat_unload, flat_load, flat_unload
        self.assertEqual(RouteGenTester.test_route.generate_extreme_decisions(), [7, 5, 5, 2, 5])
        RouteGenTester.start_station.change_charged_load(13)
        self.assertEqual(RouteGenTester.test_route.generate_extreme_decisions(), [7, 10, 0, 2, 0])
        RouteGenTester.test_vehicle.current_batteries(-8)
        self.assertEqual(RouteGenTester.test_route.generate_extreme_decisions(), [2, 10, 0, 2, 0])


if __name__ == '__main__':
    unittest.main()
