import unittest

from control import SingleElementController, ThreeElementController


class ControllerValidationTests(unittest.TestCase):

    def test_single_element_nominal_level(self):
        controller = SingleElementController()
        command = controller.update(50.0, 0.1)
        self.assertAlmostEqual(command, 1.0, places=6)

    def test_single_element_command_is_bounded(self):
        controller = SingleElementController()

        for level in (-100.0, 0.0, 50.0, 100.0, 200.0):
            command = controller.update(level, 0.1)
            self.assertGreaterEqual(command, 0.0)
            self.assertLessEqual(command, 1.5)

    def test_three_element_nominal_operation(self):
        controller = ThreeElementController()
        command = controller.update(50.0, 1.0, 1.0, 0.1)
        self.assertAlmostEqual(command, 1.0, places=6)

    def test_three_element_feedforward_response(self):
        controller = ThreeElementController()
        command = controller.update(50.0, 1.2, 1.0, 0.1)
        self.assertGreater(command, 1.0)
        self.assertLessEqual(command, 1.5)

    def test_three_element_command_is_bounded(self):
        controller = ThreeElementController()

        for level in (-100.0, 0.0, 50.0, 100.0, 200.0):
            controller.reset()
            command = controller.update(level, 1.0, 1.0, 0.1)
            self.assertGreaterEqual(command, 0.0)
            self.assertLessEqual(command, 1.5)


if __name__ == "__main__":
    unittest.main()
