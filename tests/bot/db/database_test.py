import unittest
import os
from bot.type import Order, NativeAsset, TokenAsset, AssetInfo, \
    AssetClass
from sqlalchemy.orm.session import make_transient


class TestDatabase(unittest.TestCase):

    def setUp(self):
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.db.database import Database
        from bot.db.table.user import User
        assert DB_URL == "sqlite://", "invalid DB_URL={}".format(DB_URL)

        self.db = Database()

        u1 = User("user1")
        u2 = User("user2")
        self.db.insert_or_update(u1)
        self.db.insert_or_update(u2)

    def test_get_users(self):
        users = self.db.get_users()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].id, "user1")
        self.assertEqual(users[0].sync_data, False)

    def test_insert_or_update(self):
        from bot.db.table.dca_order import DcaOrder
        orders = self.db.get_dca_orders()
        self.assertEqual(0, len(orders))

        # insert 2 new order:
        o1 = Order(5, 10, TokenAsset("Token1", "1000"),
                   AssetInfo(AssetClass.TOKEN, "token1"), 2, 500, 100)

        o2 = Order(6, 20,
                   NativeAsset("uluna", "1000"),
                   AssetInfo(AssetClass.NATIVE_TOKEN, "token2"),
                   3,
                   1000,
                   200,
                   )

        dcao1 = DcaOrder("user1", '0.1', 1, o1)
        dcao2 = DcaOrder("user1", '0.2', 2, o2)

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

    def test_log_purchase_history(self):
        self.assertEqual(0, len(self.db.get_purchase_history()))

        self.db.log_purchase_history("user1-5", 10,
                                     "initial_denom", "target_denom",
                                     1, "1-2-3", "fee_redeem",
                                     False, "err_msg")

        self.assertEqual(1, len(self.db.get_purchase_history()))

    def test_log_error(self):
        self.assertEqual(0, len(self.db.get_log_error()))

        self.db.log_error("err_msg", "calling_method",
                          "order_id", "user_address")

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
        utb1 = UserTipBalance("1", fee1)

        self.db.insert_or_update(utb1)
        tips = self.db.get_user_tip_balance()
        self.assertEqual(1, len(tips))

    def test_whitelisted_methods(self):
        from bot.db.table.whitelisted_token import WhitelistedToken
        from bot.db.table.whitelisted_hop import WhitelistedHop
        from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
        from bot.type import AstroSwap

        tokens = self.db.get_whitelisted_tokens()
        self.assertEqual(0, len(tokens))
        hops = self.db.get_whitelisted_hops()
        self.assertEqual(0, len(hops))
        fees = self.db.get_whitelisted_fee_asset()
        self.assertEqual(0, len(fees))

        ai1 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom1")
        ai2 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom2")
        ai3 = AssetInfo(AssetClass.TOKEN, "denom3")

        w1 = WhitelistedToken(ai1)
        w2 = WhitelistedToken(ai2)
        w3 = WhitelistedToken(ai3)

        self.db.insert_or_update(w1)
        self.db.insert_or_update(w2)
        self.db.insert_or_update(w3)

        tokens = self.db.get_whitelisted_tokens()
        self.assertEqual(3, len(tokens))

        astro_swap1 = AstroSwap(ai1, ai2)  # denom1 -> denom2
        astro_swap2 = AstroSwap(ai2, ai3)  # denom2 -> denom3
        ws1 = WhitelistedHop(astro_swap1)
        ws2 = WhitelistedHop(astro_swap2)
        self.db.insert_or_update(ws1)
        self.db.insert_or_update(ws2)

        hops = self.db.get_whitelisted_hops()
        self.assertEqual(2, len(hops))

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
        self.assertEqual(hops_all, expected_hops_all)

        fee1 = NativeAsset("denom1", "100")
        wfee1 = WhitelistedFeeAsset(fee1)
        self.db.insert_or_update(wfee1)
        fees = self.db.get_whitelisted_fee_asset()
        self.assertEqual(1, len(fees))


if __name__ == '__main__':
    unittest.main()
