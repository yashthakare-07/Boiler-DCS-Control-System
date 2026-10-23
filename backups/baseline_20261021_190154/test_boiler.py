import unittest
from model.boiler import BoilerModel

class BoilerTests(unittest.TestCase):
    def test_nominal_equilibrium(self):
        b = BoilerModel()
        for _ in range(1000):
            b.step(1, 1, 1)
        self.assertAlmostEqual(b.state.inventory_pu, 1.0, places=8)
        self.assertAlmostEqual(b.state.drum_level_pct, 50.0, places=6)
        self.assertAlmostEqual(b.state.pressure_pu, 1.0, places=6)

    def test_steam_step_reduces_inventory(self):
        b = BoilerModel()
        for _ in range(200):
            b.step(1, 1.2, 1)
        self.assertLess(b.state.inventory_pu, 1.0)

    def test_bounds(self):
        b = BoilerModel()
        for _ in range(5000):
            b.step(0, 1.5, 0)
        self.assertGreaterEqual(b.state.inventory_pu, 0)
        self.assertLessEqual(b.state.inventory_pu, 1.5)
        self.assertGreaterEqual(b.state.drum_level_pct, 0)
        self.assertLessEqual(b.state.drum_level_pct, 100)
        self.assertGreaterEqual(b.state.pressure_pu, 0)

    def test_bad_timestep(self):
        with self.assertRaises(ValueError):
            BoilerModel({"dt_s": 0})

if __name__ == "__main__":
    unittest.main()
