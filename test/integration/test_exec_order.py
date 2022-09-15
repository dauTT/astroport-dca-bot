import time
import unittest
import os
from bot.util import read_artifact
from terra_sdk.client.localterra import LocalTerra
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta


class TestExecOrder(unittest.TestCase):

    @staticmethod
    def setUpClass():
        os.environ['DCA_BOT'] = 'dev'
        from bot.settings import DB_URL
        from bot.settings.dev import DB_URL as DB_URL_DEV
        from bot.db_sync import initialize_db
        assert DB_URL == DB_URL_DEV, "invalid DB_URL={}".format(
            DB_URL)

        initialize_db(True)

    def setUp(self):
        os.environ['DCA_BOT'] = 'dev'
        from bot.settings import DB_URL
        from bot.settings.dev import DB_URL as DB_URL_DEV
        from bot.exec_order import ExecOrder

        assert DB_URL == DB_URL_DEV, "invalid DB_URL={}".format(
            DB_URL)

        self.network = read_artifact("localterra")
        self.dca_contract = self.network["dcaAddress"]
        terra = LocalTerra()
        self.test1_user_addr = terra.wallets["test1"].key.acc_address
        self.test2_user_addr = terra.wallets["test2"].key.acc_address
        self.test3_user_addr = terra.wallets["test3"].key.acc_address

        self.eo = ExecOrder()

        # the bot is using test1_account to interact with the dca contract.
        # the bot account is defined in the dev setting
        self.assertEqual(self.eo.dca.wallet.key.acc_address,
                         self.test1_user_addr)

    def test_purchase(self):
        # test setup:
        # test1 user has two orders
        orders = self.eo.db.get_dca_orders(user_address=self.test1_user_addr)
        self.assertEqual(len(orders), 2)
        self.assertEqual(
            orders[0].id, "terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")

        # order_0 before the purchase
        self.assertEqual(
            orders[0].token_allowance, 2000000)
        self.assertEqual(
            orders[0].initial_asset_amount, 1000000)
        self.assertEqual(
            orders[0].last_purchase, 0)
        self.assertEqual(
            orders[0].dca_amount, 10000)

        history = self.eo.db.get_purchase_history(
            "terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
        self.assertEqual(len(history), 0)

        # test1 user is executing its own order_0
        self.eo.purchase(orders[0])

        # sync data
        self.eo.sync_user_data(self.test1_user_addr)

        # check order_0 after purchase
        orders = self.eo.db.get_dca_orders(
            id="terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")

        self.assertEqual(
            orders[0].token_allowance, 1990000)
        self.assertEqual(
            orders[0].initial_asset_amount, 990000)
        self.assertGreater(
            orders[0].last_purchase.real, 0)

        # check history after purchase
        history = self.eo.db.get_purchase_history(
            "terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].success, 1)

    def test_purchase_and_sync(self):
        # test setup:
        # test1 user has two orders
        orders = self.eo.db.get_dca_orders(user_address=self.test2_user_addr)
        self.assertEqual(len(orders), 1)
        self.assertEqual(
            orders[0].id, "terra17lmam6zguazs5q5u6z5mmx76uj63gldnse2pdp-1")

        # order_0 before the purchase
        self.assertEqual(
            orders[0].token_allowance, 1000000)
        self.assertEqual(
            orders[0].initial_asset_amount, 1000000)
        self.assertEqual(
            orders[0].last_purchase, 0)
        self.assertEqual(
            orders[0].dca_amount, 250000)

        history = self.eo.db.get_purchase_history(
            "terra17lmam6zguazs5q5u6z5mmx76uj63gldnse2pdp-1")
        self.assertEqual(len(history), 0)

        # test1 user is executing its own order_0
        self.eo.purchase_and_sync(
            order_id="terra17lmam6zguazs5q5u6z5mmx76uj63gldnse2pdp-1")

        # check order_0 after purchase
        orders = self.eo.db.get_dca_orders(
            id="terra17lmam6zguazs5q5u6z5mmx76uj63gldnse2pdp-1")

        self.assertEqual(
            orders[0].token_allowance, 750000)
        self.assertEqual(
            orders[0].initial_asset_amount, 750000)
        self.assertGreater(
            orders[0].last_purchase.real, 0)

        # check history after purchase
        history = self.eo.db.get_purchase_history(
            "terra17lmam6zguazs5q5u6z5mmx76uj63gldnse2pdp-1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].success, 1)

    def test_schedule_next_run(self):
        """ test the execution of an order till it is fully complete.
        """
        # setup test:
        orders = self.eo.db.get_dca_orders(
            "terra1757tkx08n0cqrw7p86ny9lnxsqeth0wgp0em95-1")

        self.assertEqual(orders[0].initial_asset_amount, 1000000)
        self.assertEqual(orders[0].dca_amount, 500000)
        self.assertEqual(orders[0].schedule, False)
        self.assertEqual(orders[0].next_run_time, None)

        history = self.eo.db.get_purchase_history(
            "terra1757tkx08n0cqrw7p86ny9lnxsqeth0wgp0em95-1")
        self.assertEqual(len(history), 0)

        # create scheduler
        scheduler = BackgroundScheduler(timezone='utc')

        self.eo.schedule_next_run(orders, scheduler)
        scheduler.start()

        self.assertEqual(orders[0].schedule, True)
        self.assertIsNotNone(orders[0].next_run_time)

        # wait till the order is completely executed.
        # Once it is completed, it will be removed from the order table.
        len_orders = len(orders)
        history_entries = 0
        db_next_run_time = None
        while len_orders > 0:
            orders = self.eo.db.get_dca_orders(
                "terra1757tkx08n0cqrw7p86ny9lnxsqeth0wgp0em95-1")
            len_orders = len(orders)
            if len_orders > 0:
                if db_next_run_time != orders[0].next_run_time:
                    db_next_run_time = orders[0].next_run_time
                    print("db_next_run_time: {}".format(
                        db_next_run_time))

                if db_next_run_time != None:
                    assert datetime.utcnow() + \
                        timedelta(
                            seconds=20) > db_next_run_time, "db next_run_time = {} is expired!".format(db_next_run_time)

                history = self.eo.db.get_purchase_history(
                    "terra1757tkx08n0cqrw7p86ny9lnxsqeth0wgp0em95-1")
                if len(history) != history_entries:
                    print("""current purchase executed: success={}
                             nr purhchases:{}
                    """.format(history[len(history)-1].success, len(history)))
                    history_entries = len(history)

                print("sleep 10")
                time.sleep(10)
            else:
                print("finish purchases!")

        # we expect the bot two execute two successful purchases because:
        # - initial_asset_amount = 1000000
        # - dca_amount = 500000
        self.assertGreaterEqual(history_entries, 1)

        # After the second successful purchase the order is fully completed and it will be removed
        # from the db:
        orders = self.eo.db.get_dca_orders(
            "terra1757tkx08n0cqrw7p86ny9lnxsqeth0wgp0em95-1")
        self.assertEqual(0, len(orders))

        # The removal of the order_id = "terra1757tkx08n0cqrw7p86ny9lnxsqeth0wgp0em95-1" from the order table
        # will cause the deletion of the corresponding entries in the purchase history table:
        history = self.eo.db.get_purchase_history(
            "terra1757tkx08n0cqrw7p86ny9lnxsqeth0wgp0em95-1")
        self.assertEqual(0, len(history))

        print("*********** shutdown scheduler ***********")
        scheduler.shutdown(wait=False)
        print("*********** FINISH ***********")


if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.INFO)
    testNames = [
        "test_purchase",
        "test_purchase_and_sync",
        "test_schedule_next_run",
    ]

    testFullNames = [
        "test_exec_order.TestExecOrder.{}".format(t) for t in testNames]

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
    pass
