import unittest

from calculator import Calculator


class TestCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = Calculator()

    def test_add(self):
        self.assertEqual(self.calculator.add(2, 3), 5)

    def test_subtract(self):
        self.assertEqual(self.calculator.subtract(10, 4), 6)

    def test_multiply(self):
        self.assertEqual(self.calculator.multiply(6, 7), 42)

    def test_divide(self):
        self.assertEqual(self.calculator.divide(20, 4), 5)

    def test_power(self):
        self.assertEqual(self.calculator.power(2, 5), 32)


if __name__ == "__main__":
    unittest.main()