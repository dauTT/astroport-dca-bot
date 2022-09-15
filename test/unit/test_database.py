import unittest
import os
from bot.type import Order, NativeAsset, TokenAsset, AssetInfo, \
    AssetClass
from sqlalchemy.orm.session import make_transient
from datetime import datetime, timedelta


TEST_USER_1 = "user1_addr"
TEST_USER_2 = "user2_addr"

ORDER_1 = Order(5, 10, TokenAsset("Token1", "1000"),
                AssetInfo(AssetClass.TOKEN, "token1"), 2, 500, 100)

ORDER_2 = Order(6, 20,
                NativeAsset("uluna", "1000"),
                AssetInfo(AssetClass.NATIVE_TOKEN, "token2"),
                3,
                1000,
                200,
                )

ORDER_3 = Order(7, 20,
                NativeAsset("uluna", "1000"),
                AssetInfo(AssetClass.NATIVE_TOKEN, "token2"),
                3,
                1000,
                200,
                )


class TestDatabase(unittest.TestCase):

    # @staticmethod
    # def setUpClass():
    #     os.environ['DCA_BOT'] = 'test'
    #     from bot.settings import DB_URL
    #     from bot.settings.test import DB_URL as DB_URL_TEST
    #     from bot.db.database import create_database_objects, Database
    #     from bot.db.table.user import User

    #     assert DB_URL == DB_URL_TEST, "invalid DB_URL={}".format(
    #         DB_URL)

    #     create_database_objects()

    #     db = Database()

    def setUp(self):
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.settings.test import DB_URL as DB_URL_TEST
        from bot.db.database import Database, create_database_objects
        from bot.db.table.user import User
        assert DB_URL == DB_URL_TEST, "invalid DB_URL={}".format(
            DB_URL)

        create_database_objects()
        self.db = Database()

        u1 = User(TEST_USER_1)
        u2 = User(TEST_USER_2)
        self.db.insert_or_update(u1)
        self.db.insert_or_update(u2)

    @classmethod
    def tearDownClass(cls):
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.db.database import drop_database_objects

        drop_database_objects()

    def test_get_users(self):
        users = self.db.get_users()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].id, TEST_USER_1)
        self.assertEqual(users[0].sync_data, False)

    def test_delete_on_cascade_dca_order(self):
        from bot.db.table.dca_order import DcaOrder
        from bot.db.table.user import User

        # check we have the two uses: TEST_USER_1, TEST_USER_2
        users = self.db.get_users()
        self.assertEqual(2, len(users))

        # setup test
        dcao1 = DcaOrder(TEST_USER_1, '0.1', 1, ORDER_1)
        dcao2 = DcaOrder(TEST_USER_2, '0.2', 2, ORDER_2)
        dcao3 = DcaOrder(TEST_USER_2, '0.2', 3, ORDER_3)

        self.db.insert_or_update(dcao1)
        self.db.insert_or_update(dcao2)
        self.db.insert_or_update(dcao3)

        self.assertEqual(3, len(self.db.get_dca_orders()))

        # delete TEST_USER_2
        self.db.delete(User, User.id == TEST_USER_2)

        users = self.db.get_users()
        self.assertEqual(1, len(users))

        # Check the orders of TEST_USER_2 has been deleted as well
        orders = self.db.get_dca_orders()
        self.assertEqual(1, len(orders))
        self.assertEqual(dcao1.id, orders[0].id)

        # clean order table
        self.db.exec_sql("delete from dca_order")
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))

    def test_delete_on_cascade_log_error(self):
        from bot.db.table.user import User

        # check we have the two uses: TEST_USER_1, TEST_USER_2
        users = self.db.get_users()
        self.assertEqual(2, len(users))

        # Check the are no log error
        self.assertEqual(0, len(self.db.get_log_error()))

        # Enter three log error
        self.db.log_error(
            "err_msg1", "test_delete_on_cascade_log_error", None, TEST_USER_1)
        self.db.log_error(
            "err_msg2", "test_delete_on_cascade_log_error", None, TEST_USER_2)
        self.db.log_error(
            "err_msg3", "test_delete_on_cascade_log_error", None, TEST_USER_2)

        self.assertEqual(3, len(self.db.get_log_error()))

        # delete TEST_USER_2
        self.db.delete(User, User.id == TEST_USER_2)

        users = self.db.get_users()
        self.assertEqual(1, len(users))

        # Check the log errors of TEST_USER_2 has been deleted as well
        log_errors = self.db.get_log_error()
        self.assertEqual(1, len(log_errors))
        self.assertEqual(TEST_USER_1, log_errors[0].user_address)

        # clean log_errors table
        self.db.exec_sql("delete from log_error")
        log_errors = self.db.get_log_error()
        self.assertEqual(0, len(log_errors))

    def test_delete_on_cascade_purchase_history(self):
        from bot.db.table.user import User
        from bot.db.table.dca_order import DcaOrder

        # check we have the two uses: TEST_USER_1, TEST_USER_2
        users = self.db.get_users()
        self.assertEqual(2, len(users))

        # check the are no history entry
        self.assertEqual(0, len(self.db.get_purchase_history()))

        dcao1 = DcaOrder(TEST_USER_1, '0.1', 1, ORDER_1)
        self.db.insert_or_update(dcao1)

        # enter one history entry
        self.db.log_purchase_history(str(dcao1.id), dcao1.initial_asset_amount.real, str(dcao1.initial_asset_denom),
                                     str(dcao1.target_asset_denom), dcao1.dca_amount.real, "", "", False, "err_mdg")

        self.assertEqual(1, len(self.db.get_purchase_history()))

        # delete dcao1
        self.db.delete(DcaOrder, DcaOrder.id == DcaOrder.id)
        self.assertEqual(0, len(self.db.get_dca_orders()))

        # check the purchase history of TEST_USER_1 has been deleted as well
        history = self.db.get_purchase_history()
        self.assertEqual(0, len(history))

    def test_delete_on_cascade_purchase_history2(self):
        from bot.db.table.user import User
        from bot.db.table.dca_order import DcaOrder

        # check we have the two uses: TEST_USER_1, TEST_USER_2
        users = self.db.get_users()
        self.assertEqual(2, len(users))

        # check the are no history entry
        self.assertEqual(0, len(self.db.get_purchase_history()))

        dcao1 = DcaOrder(TEST_USER_1, '0.1', 1, ORDER_1)
        dcao2 = DcaOrder(TEST_USER_1, '0.1', 1, ORDER_2)
        self.db.insert_or_update(dcao1)
        self.db.insert_or_update(dcao2)

        # enter 3 history entries
        self.db.log_purchase_history(str(dcao1.id), dcao1.initial_asset_amount.real, str(dcao1.initial_asset_denom),
                                     str(dcao1.target_asset_denom), dcao1.dca_amount.real, "", "", False, "err_mdg")
        self.db.log_purchase_history(str(dcao1.id), 1000, "denom2",
                                     "denom3", 10, "", "", False, "err_mdg")
        self.db.log_purchase_history(str(dcao2.id), 1000, "denom2",
                                     "denom3", 10, "", "", False, "err_mdg")

        self.assertEqual(3, len(self.db.get_purchase_history()))

        # delete dca1
        self.db.delete(DcaOrder, (DcaOrder.user_address == TEST_USER_1) & (  # type: ignore
            DcaOrder.id.not_in([dcao2.id])))  # type: ignore

        orders = self.db.get_dca_orders()
        self.assertEqual(1, len(orders))
        self.assertEqual(dcao2.id, orders[0].id)

        # check the purchase history of TEST_USER_1 has been deleted as well
        history = self.db.get_purchase_history()
        self.assertEqual(1, len(history))

        self.assertEqual(str(dcao2.id), history[0].order_id)

        # clean history table
        self.db.exec_sql("delete from purchase_history")
        self.db.exec_sql("delete from dca_order")
        history = self.db.get_purchase_history()
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(history))
        self.assertEqual(0, len(orders))

    def test_insert_or_update(self):
        from bot.db.table.dca_order import DcaOrder
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))

        dcao1 = DcaOrder(TEST_USER_1, '0.1', 1, ORDER_1)
        dcao2 = DcaOrder(TEST_USER_1, '0.2', 2, ORDER_2)

        self.db.insert_or_update(dcao1)
        self.db.insert_or_update(dcao2)

        # insert_or_update will actuall execute an update
        # if the primary key id stay the same
        orders = self.db.get_dca_orders()
        self.assertEqual(2, len(orders))

        make_transient(orders[0])

        # update only field initial_asset_amount
        self.assertEqual(1000, orders[0].initial_asset_amount)
        orders[0].initial_asset_amount = 2000
        self.db.insert_or_update(orders[0])
        orders = self.db.get_dca_orders()
        self.assertEqual(2, len(orders))

        order_updated = self.db.get_dca_orders(str(orders[0].id))
        self.assertEqual(orders[0].id, order_updated[0].id)
        self.assertEqual(orders[0].create_at, order_updated[0].create_at)
        self.assertEqual(2000,      order_updated[0].initial_asset_amount)
        self.assertEqual(orders[0].initial_asset_class,
                         order_updated[0].initial_asset_class)
        self.assertEqual(orders[0].interval, order_updated[0].interval)
        self.assertEqual(orders[0].dca_amount, order_updated[0].dca_amount)
        self.assertEqual(orders[0].last_purchase,
                         order_updated[0].last_purchase)
        self.assertEqual(orders[0].max_hops, order_updated[0].max_hops)
        self.assertEqual(orders[0].max_spread, order_updated[0].max_spread)

        # if the order_id is new we expected the method insert_or_update to actually insert.
        make_transient(orders[0])

        orders[0].id = "order_id_new"
        self.db.insert_or_update(orders[0])
        orders = self.db.get_dca_orders()
        # the numner of orders has incremented of one
        self.assertEqual(3, len(orders))

        # empty dca_order table
        self.db.delete(DcaOrder, DcaOrder.id.in_(  # type: ignore
            [orders[0].id, orders[1].id, orders[2].id]))  # type: ignore

        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))

    def test_expired_next_run_time_flag(self):
        from bot.db.table.dca_order import DcaOrder
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))

        dcao1 = DcaOrder(TEST_USER_1, '0.1', 1, ORDER_1)
        dcao2 = DcaOrder(TEST_USER_1, '0.2', 2, ORDER_2)

        dcao1.next_run_time = datetime.utcnow() + timedelta(seconds=120)
        dcao2.next_run_time = datetime.utcnow() - timedelta(seconds=1)

        self.db.insert_or_update(dcao1)
        self.db.insert_or_update(dcao2)

        # insert_or_update will actuall execute an update
        # if the primary key id stay the same
        orders = self.db.get_dca_orders(expired_next_run_time=False)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, dcao1.id)

        orders = self.db.get_dca_orders(expired_next_run_time=True)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, dcao2.id)

        # clean order table
        self.db.exec_sql("delete from dca_order")
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))

    def test_log_purchase_history(self):
        from bot.db.table.dca_order import DcaOrder
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))

        # setup test
        o1 = Order(5, 10, TokenAsset("Token1", "1000"),
                   AssetInfo(AssetClass.TOKEN, "token1"), 2, 500, 100)
        dcao1 = DcaOrder(TEST_USER_1, '0.1', 1, o1)

        self.db.insert_or_update(dcao1)

        # check no history
        self.assertEqual(0, len(self.db.get_purchase_history()))

        # insert one entry in history table
        self.db.log_purchase_history(str(dcao1.id), 10,
                                     "initial_denom", "target_denom",
                                     1, "1-2-3", "fee_redeem",
                                     False, "err_msg")

        # check there is one entry in history table
        self.assertEqual(1, len(self.db.get_purchase_history()))

        # clean  tables
        self.db.exec_sql(
            "delete from dca_order")
        self.db.exec_sql(
            "delete from purchase_history")
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))
        history = self.db.get_purchase_history()
        self.assertEqual(0, len(history))

    def test_log_error(self):
        self.assertEqual(0, len(self.db.get_log_error()))

        self.db.log_error("err_msg", "calling_method",
                          None, TEST_USER_1)

        self.assertEqual(1, len(self.db.get_log_error()))

    def test_sql_query(self):
        orders = self.db.get_dca_orders()
        output = self.db.sql_query("select * from dca_order")
        self.assertEqual(len(orders), len(output))

    def test_get_tables_names(self):
        names = self.db.get_tables_names()
        self.assertGreater(len(names), 1)

    def test_get_user_tip_balance(self):
        from bot.db.table.user_tip_balance import UserTipBalance
        tips = self.db.get_user_tip_balance()
        self.assertEqual(0, len(tips))

        fee1 = NativeAsset("denom1", "100")
        utb1 = UserTipBalance(TEST_USER_1, fee1)

        self.db.insert_or_update(utb1)
        tips = self.db.get_user_tip_balance()
        self.assertEqual(1, len(tips))

    def test_whitelisted_methods(self):
        from bot.db.table.whitelisted_token import WhitelistedToken
        from bot.db.table.whitelisted_hop import WhitelistedHop
        from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
        from bot.type import AstroSwap

        # check whitelisted table are empty
        tokens = self.db.get_whitelisted_tokens()
        self.assertEqual(0, len(tokens))
        hops = self.db.get_whitelisted_hops()
        self.assertEqual(0, len(hops))
        fees = self.db.get_whitelisted_fee_asset()
        self.assertEqual(0, len(fees))

        # insert three witelisted assets
        ai1 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom1")
        ai2 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom2")
        ai3 = AssetInfo(AssetClass.TOKEN, "denom3")

        w1 = WhitelistedToken(ai1)
        w2 = WhitelistedToken(ai2)
        w3 = WhitelistedToken(ai3)

        self.db.insert_or_update(w1)
        self.db.insert_or_update(w2)
        self.db.insert_or_update(w3)

        # check the  tokens are there in the db
        tokens = self.db.get_whitelisted_tokens()
        self.assertEqual(3, len(tokens))

        # insert 2 hops
        astro_swap1 = AstroSwap(ai1, ai2)  # denom1 -> denom2
        astro_swap2 = AstroSwap(ai2, ai3)  # denom2 -> denom3
        ws1 = WhitelistedHop(astro_swap1)
        ws2 = WhitelistedHop(astro_swap2)
        self.db.insert_or_update(ws1)
        self.db.insert_or_update(ws2)

        # check the hops are there in the db
        hops = self.db.get_whitelisted_hops()
        self.assertEqual(2, len(hops))

        # check the get_whitelisted_hops_all view:
        hops_all = self.db.get_whitelisted_hops_all()
        expected_hops_all = [{'start_denom': 'denom1', 'id': '1', 'hops_len': 1,
                              'target_denom': 'denom2', 'hops': '<1>'},

                             {'start_denom': 'denom2', 'id': '2', 'hops_len': 1,
                             'target_denom': 'denom3', 'hops': '<2>'},

                             {'start_denom': 'denom2', 'id': 'inverse-1', 'hops_len': 1,
                             'target_denom': 'denom1', 'hops': '<inverse-1>'},

                             {'start_denom': 'denom3', 'id': 'inverse-2', 'hops_len': 1,
                              'target_denom': 'denom2', 'hops': '<inverse-2>'},

                             {'start_denom': 'denom1', 'id': '2', 'hops_len': 2,
                              'target_denom': 'denom3', 'hops': '<1><2>'},

                             {'start_denom': 'denom3', 'id': '1', 'hops_len': 2,
                                 'target_denom': 'denom2', 'hops': '<inverse-2><inverse-1>'},
                             ]
        expected_list_hops_string = [
            '<1>', '<2>', '<1><2>', '<inverse-1>', '<inverse-2>', '<inverse-2><inverse-1>']
        actual_list_hops_string = [h['hops'] for h in hops_all]
        actual_list_hops_string.sort()
        expected_list_hops_string.sort()

        self.assertEqual(actual_list_hops_string,
                         expected_list_hops_string)
        self.assertEqual(hops_all, expected_hops_all)

        self.assertEqual('<2>', self.db.get_whitelisted_hops_all(
            "denom2", "denom3")[0]['hops'])
        self.assertEqual('<inverse-2>', self.db.get_whitelisted_hops_all(
            "denom3", "denom2")[0]['hops'])

        # insert one fee asset
        fee1 = NativeAsset("denom1", "100")
        wfee1 = WhitelistedFeeAsset(fee1)
        self.db.insert_or_update(wfee1)

        # check the fee is there in the db
        fees = self.db.get_whitelisted_fee_asset()
        self.assertEqual(1, len(fees))


def get_test_names():
    testNames = [
        "test_get_users",
        "test_delete_on_cascade_dca_order",
        "test_delete_on_cascade_log_error",
        "test_delete_on_cascade_purchase_history",
        "test_delete_on_cascade_purchase_history2",
        "test_insert_or_update",
        "test_expired_next_run_time_flag",
        "test_log_purchase_history",
        "test_log_error",
        "test_sql_query",
        "test_get_tables_names",
        "test_get_user_tip_balance",
        "test_whitelisted_methods"
    ]
    testFullNames = [
        "test_database.TestDatabase.{}".format(t) for t in testNames]
    return testFullNames


if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    testFullNames = get_test_names()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
