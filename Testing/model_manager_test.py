import unittest
from Station import Station
from Subproblem.model_manager import ModelManager
import numpy as np


class ModelManagerTester(unittest.TestCase):

    test_station = Station(longitude=59.9306, latitude=10.714780000000001, charged_load=5, flat_load=2,
                           incoming_charged_bike_rate=0.04, incoming_flat_bike_rate=0.017,
                           outgoing_charged_bike_rate=0.051, ideal_state=10, station_id='386',
                           station_cap=20, charging=False)

    test_manager = ModelManager('386')

    def test_base_violation(self):
        self.assertEqual(ModelManager.get_base_violations(ModelManagerTester.test_station, visit_inventory_charged=10,
                                                          visit_inventory_flat=5, customer_arrivals=[10, 3, 2]), 6)
        self.assertEqual(ModelManager.get_base_violations(ModelManagerTester.test_station, visit_inventory_charged=0,
                                                          visit_inventory_flat=0, customer_arrivals=[0, 0, 2]), 2)
        self.assertEqual(ModelManager.get_base_violations(ModelManagerTester.test_station, visit_inventory_charged=0,
                                                          visit_inventory_flat=0, customer_arrivals=[0, 21, 2]), 3)
        self.assertEqual(ModelManager.get_base_violations(ModelManagerTester.test_station, visit_inventory_charged=6,
                                                          visit_inventory_flat=5, customer_arrivals=[2, 15, 8]), 0)
        self.assertEqual(ModelManager.get_base_violations(ModelManagerTester.test_station, visit_inventory_charged=1,
                                                          visit_inventory_flat=15, customer_arrivals=[5, 15, 7]), 11)

    def test_base_inventory(self):
        self.assertEqual(ModelManager.get_base_inventory(station=ModelManagerTester.test_station, visit_time_float=5,
                                                         customer_arrivals=[[], [], []]), (5, 2))
        self.assertEqual(ModelManager.get_base_inventory(station=ModelManagerTester.test_station, visit_time_float=5,
                                                         customer_arrivals=[[1, 2, 3], [2, 4], [0]]), (7, 4))
        self.assertEqual(ModelManager.get_base_inventory(station=ModelManagerTester.test_station, visit_time_float=10,
                                                         customer_arrivals=[[1, 1, 1, 1, 4, 5, 2, 3], [2, 3, 4, 9, 4, 9],
                                                                            []]), (13, 7))
        self.assertEqual(ModelManager.get_base_inventory(station=ModelManagerTester.test_station, visit_time_float=10,
                                                         customer_arrivals=[[1, 1, 1, 1, 4, 5, 2, 3, 9], [2, 3, 4, 9, 4, 9],
                                                                            []]), (14, 6))
        self.assertEqual(ModelManager.get_base_inventory(station=ModelManagerTester.test_station, visit_time_float=15,
                                                         customer_arrivals=[[], [2, 3, 4, 9, 4, 9],
                                                                            [0, 4, 5, 8, 10, 11, 1]]), (0, 8))

    def test_poisson_draw(self):
        route = ModelManagerTester.test_manager.gen.finished_gen_routes[1]
        draw_1 = ModelManager.poisson_draw(route)
        self.assertEqual(np.shape(draw_1), (len(route.stations), 3))
        self.assertEqual(draw_1[-1], [0, 0, 0])
        self.assertIsInstance(draw_1[1][1], int)


if __name__ == '__main__':
    unittest.main()
