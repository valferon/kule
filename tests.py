import unittest

from kule import Kule


class KuleTests(unittest.TestCase):

    def setUp(self):
        self.kule = Kule(database="test")

unittest.main()

