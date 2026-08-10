import unittest
from decimal import Decimal as D
from allocation import Usage,allocate_shared,budget_status

USAGE=[Usage("A",600,D("3600"),D("100")),Usage("B",300,D("1800"),D("300")),Usage("C",100,D("600"),D("100"))]

class AllocationTest(unittest.TestCase):
    def test_conserves_every_cent(self): self.assertEqual(D("1000.00"),sum(allocate_shared(D("1000.00"),USAGE,(D(".4"),D(".4"),D(".2"))).values()))
    def test_expected_weighted_allocation(self):
        self.assertEqual({"A":D("520.00"),"B":D("360.00"),"C":D("120.00")},allocate_shared(D("1000"),USAGE,(D(".4"),D(".4"),D(".2"))))
    def test_rounding_conserves(self):
        equal=[Usage(x,1,D(1),D(1)) for x in "ABC"]
        self.assertEqual({"A":D("0.34"),"B":D("0.33"),"C":D("0.33")},allocate_shared(D("1.00"),equal,(D(1),D(0),D(0))))
    def test_invalid_weights(self):
        with self.assertRaises(ValueError): allocate_shared(D(1),USAGE,(D(".5"),D(".5"),D(".1")))
    def test_budget_states(self):
        self.assertEqual("OK",budget_status(D(70),D(100),D(90)))
        self.assertEqual("WATCH",budget_status(D(80),D(100),D(95)))
        self.assertEqual("FORECAST_BREACH",budget_status(D(70),D(100),D(110)))
        self.assertEqual("EXCEEDED",budget_status(D(101),D(100),D(110)))
    def test_zero_weighted_driver_rejected(self):
        with self.assertRaises(ValueError): allocate_shared(D(1),[Usage("A",1,D(0),D(1))],(D(0),D(1),D(0)))

if __name__ == "__main__": unittest.main()
