import unittest
from Station import Station
from vehicle import Vehicle


class StationVehicleTester(unittest.TestCase):

    test_station = Station(longitude=59.9306, latitude=10.714780000000001, charged_load=5, flat_load=2,
                           incoming_charged_bike_rate=0.04, incoming_flat_bike_rate=0.017,
                           outgoing_charged_bike_rate=0.051, ideal_state=10, station_id='386',
                           station_cap=10, charging=False)

    test_vehicle = Vehicle(init_battery_load=10, init_charged_bikes=5, init_flat_bikes=5, bike_cap=20, bat_cap=20)

    def test_station_inventory(self):
        self.assertEqual(StationVehicleTester.test_station.current_charged_bikes, 5)
        self.assertEqual(StationVehicleTester.test_station.current_flat_bikes, 2)
        self.assertEqual(StationVehicleTester.test_station.available_parking(), 13)
        StationVehicleTester.test_station.change_charged_load(-6)
        self.assertEqual(StationVehicleTester.test_station.current_charged_bikes, 0)
        StationVehicleTester.test_station.change_charged_load(15)
        self.assertEqual(StationVehicleTester.test_station.current_charged_bikes, 8)
        StationVehicleTester.test_station.change_flat_load(15)
        self.assertEqual(StationVehicleTester.test_station.current_flat_bikes, 2)
        StationVehicleTester.test_station.change_flat_load(-15)
        self.assertEqual(StationVehicleTester.test_station.current_flat_bikes, 0)

    def test_vehicle_inventory(self):
        self.assertEqual(StationVehicleTester.test_vehicle.current_batteries, 10)
        self.assertEqual(StationVehicleTester.test_vehicle.current_charged_bikes, 5)
        self.assertEqual(StationVehicleTester.test_vehicle.current_flat_bikes, 5)
        StationVehicleTester.test_vehicle.change_battery_bikes(-4)
        self.assertEqual(StationVehicleTester.test_vehicle.available_bike_capacity(), 14)
        StationVehicleTester.test_vehicle.change_battery_bikes(5)
        self.assertEqual(StationVehicleTester.test_vehicle.available_bike_capacity(), 9)
        StationVehicleTester.test_vehicle.swap_batteries(4)
        self.assertEqual(StationVehicleTester.test_vehicle.current_batteries, 6)


if __name__ == '__main__':
    unittest.main()
