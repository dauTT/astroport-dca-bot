import unittest
from test.integration.test_dca import TestDca


if __name__ == "__main__":
    suiteA = unittest.TestLoader().loadTestsFromTestCase(TestDca)
    #suiteB = unittest.TestLoader().loadTestsFromTestCase(TestDF)
    suite = unittest.TestSuite([suiteA,
                                # suiteB
                                ])
    runner = unittest.TextTestRunner()
    runner.run(suite)
