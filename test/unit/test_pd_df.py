import unittest
import os
from bot.type import Order, NativeAsset, TokenAsset, AssetInfo, \
    AssetClass


# @unittest.skip("skipping TestDF due to conflicts with TestDatabase.")
class TestDF(unittest.TestCase):

    @staticmethod
    def setUpClass():
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.settings.test import DB_URL as DB_URL_TEST
        from bot.db.table.dca_order import DcaOrder
        from bot.db.database import Database, create_database_objects
        from bot.db.table.user import User
        from bot.db.table.user_tip_balance import UserTipBalance
        from bot.db.table.whitelisted_token import WhitelistedToken
        from bot.db.table.whitelisted_hop import WhitelistedHop
        from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
        from bot.type import AstroSwap

        assert DB_URL == DB_URL_TEST, "invalid DB_URL={}".format(
            DB_URL)

        create_database_objects()
        db = Database()

        u1 = User("user1")
        User("user2")
        db.insert_or_update(u1)

        o1 = Order(5, 10, TokenAsset("Token1", "1000"),
                   AssetInfo(AssetClass.TOKEN, "token1"), 2, 500, 100)

        dcao1 = DcaOrder("user1", '0.1', 1, o1)
        db.insert_or_update(dcao1)

        db.log_error("err_msg", "calling_method",
                     "order_id", "user_address")

        db.log_purchase_history("user1-5", 10,
                                "initial_denom", "target_denom",
                                1, "1-2-3", "fee_redeem",
                                False, "err_msg")
        fee1 = NativeAsset("denom1", "100")
        utb1 = UserTipBalance("1", fee1)

        db.insert_or_update(utb1)

        ai1 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom1")
        w1 = WhitelistedToken(ai1)
        db.insert_or_update(w1)

        ai2 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom2")
        astro_swap1 = AstroSwap(ai1, ai2)  # denom1 -> denom2
        wh = WhitelistedHop(astro_swap1)
        db.insert_or_update(wh)

        fee1 = NativeAsset("denom1", "100")
        wfee1 = WhitelistedFeeAsset(fee1)
        db.insert_or_update(wfee1)

    @classmethod
    def tearDownClass(cls):
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.db.database import drop_database_objects

        drop_database_objects()

    def setUp(self):
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.settings.test import DB_URL as DB_URL_TEST
        from bot.db.pd_df import DF
        from bot.db.database import Database
        assert DB_URL == DB_URL_TEST, "invalid DB_URL={}".format(
            DB_URL)

        self.df = DF()
        self.db = Database()

    def test_user(self):
        self.assertEqual(1, len(self.df.user))

    def test_dca_order(self):
        self.assertEqual(1, len(self.df.dca_order))

    def test_log_error(self):
        self.assertEqual(1, len(self.df.log_error))

    def test_purchase_history(self):
        self.assertEqual(1, len(self.df.purchase_history))

    def test_user_tip_balance(self):
        self.assertEqual(1, len(self.df.user_tip_balance))

    def test_whitelisted_fee_asset(self):
        self.assertEqual(1, len(self.df.whitelisted_fee_asset))

    def test_whitelisted_token(self):
        self.assertEqual(1, len(self.df.whitelisted_token))

    def test_whitelisted_hop(self):
        self.assertEqual(1, len(self.df.whitelisted_hop))

    def test_convert_to_df(self):
        df_users = self.df.convert_to_df(self.db.get_users())
        self.assertEqual(1, len(df_users))


def get_test_names():
    testNames = [
        "test_user",
        "test_dca_order",
        "test_log_error",
        "test_purchase_history",
        "test_user_tip_balance",
        "test_whitelisted_fee_asset",
        "test_whitelisted_token",
        "test_whitelisted_hop",
        "test_convert_to_df",
    ]
    testFullNames = ["test_pd_df.TestDF.{}".format(t) for t in testNames]
    return testFullNames


if __name__ == '__main__':
    testFullNames = get_test_names()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
