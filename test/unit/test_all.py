import unittest
from test.unit.test_database import get_test_names as test_db_names
from test.unit.test_pd_df import get_test_names as test_df_names
from test.unit.test_db_sync import get_test_names as test_sync_names
from test.unit.test_exec_order import get_test_names as test_exec_order_names


def get_test_names():
    testFullNames = test_df_names() + test_db_names() + \
        test_sync_names() + test_exec_order_names()
    return testFullNames


if __name__ == "__main__":
    testFullNames = get_test_names()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
