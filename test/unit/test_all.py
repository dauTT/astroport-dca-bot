import unittest
from test.unit.test_database import TestDatabase
from test.unit.test_pd_df import TestDF


if __name__ == "__main__":
    suiteA = unittest.TestLoader().loadTestsFromTestCase(TestDatabase)
    suiteB = unittest.TestLoader().loadTestsFromTestCase(TestDF)
    suite = unittest.TestSuite([suiteA, suiteB])
    runner = unittest.TextTestRunner()
    runner.run(suite)
