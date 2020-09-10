import pprint
import unittest

class TokexTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def _debug(self, *args):
        pprint.pprint(*args)
