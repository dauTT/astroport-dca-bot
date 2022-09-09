# import unittest
# from test.unit.test_database import TestDatabase
# from test.unit.test_pd_df import TestDF
# from test.unit.test_db_sync import TestDbSync


# if __name__ == "__main__":
#     suiteA = unittest.TestLoader().loadTestsFromTestCase(TestDatabase)
#     suiteB = unittest.TestLoader().loadTestsFromTestCase(TestDF)
#     # suiteC = unittest.TestLoader().loadTestsFromTestCase(TestDbSync)
#     suite = unittest.TestSuite([suiteA, suiteB])
#     runner = unittest.TextTestRunner()
#     runner.run(suite)


import unittest
from test.unit.test_database import get_test_names as test_db_names
from test.unit.test_pd_df import get_test_names as test_df_names
from test.unit.test_db_sync import get_test_names as test_sync_names


def get_test_names():
    testFullNames = test_df_names() + test_db_names() + test_sync_names()
    return testFullNames


if __name__ == "__main__":
    testFullNames = get_test_names()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    # pass
