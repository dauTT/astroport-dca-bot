
import unittest
import os
from unittest.mock import Mock
from bot.type import NativeAsset, TokenAsset
from terra_sdk.client.localterra import LocalTerra


TOKEN1 = TokenAsset("denom1", "1000")
TOKEN2 = TokenAsset("denom2", "2000")
TOKEN3 = TokenAsset("denom3", "3000")
TOKEN4 = TokenAsset("denom4", "4000")
LUNA = NativeAsset("uluna", "5000")

TEST_USER = "user_address"


def mock_dca():
    mock = Mock()

    mock.query_get_config.return_value = {
        'max_hops': 3,
        'max_spread': '0.5',
        'whitelisted_fee_assets': [TOKEN1.get_asset(),
                                   LUNA.get_asset()],
        'whitelisted_tokens': [TOKEN1.get_info().to_dict(),
                               TOKEN2.get_info().to_dict(),
                               TOKEN3.get_info().to_dict(),
                               LUNA.get_info().to_dict()],
        'factory_addr': 'factory_addr',
        'router_addr': 'router_addr'

    }

    mock.get_astro_pools.return_value = {
        'pairs': [
            {'asset_infos': [TOKEN1.get_info().to_dict(), TOKEN2.get_info().to_dict()],
                'contract_addr': 'contract_addr_1',
                'liquidity_token': 'liquidity_token_1',
                'pair_type': {'xyk': {}}},

            {'asset_infos': [TOKEN2.get_info().to_dict(), TOKEN3.get_info().to_dict()],
             'contract_addr': 'contract_addr2',
                'liquidity_token': 'liquidity_token2',
                'pair_type': {'xyk': {}}},

            {'asset_infos': [TOKEN4.get_info().to_dict(), LUNA.get_info().to_dict()],
                'contract_addr': 'contract_addr3',
                'liquidity_token': 'liquidity_token3',
                'pair_type': {'stable': {}}},

            {'asset_infos': [LUNA.get_info().to_dict(), TOKEN3.get_info().to_dict()],
                'contract_addr': 'contract_addr4',
                'liquidity_token': 'liquidity_token4',
                'pair_type': {'xyk': {}}}]

    }

    mock.query_get_user_config.return_value = {
        'last_id': 1,
        'max_hops': None,
        'max_spread': None,
        'tip_balance': [TOKEN1.get_asset(), LUNA.get_asset()]

    }

    mock.query_get_user_dca_orders.return_value = [{'token_allowance': '1000000',
                                                    'order': {'id': 1,
                                                              'initial_asset':  TOKEN1.get_asset(),
                                                              'target_asset':  LUNA.get_info().to_dict(),
                                                              'interval': 5,
                                                              'last_purchase': 0,
                                                              'dca_amount': '250000'}},

                                                   {'token_allowance': '2000000',
                                                    'order': {'id': 2,
                                                              'initial_asset':  TOKEN1.get_asset(),
                                                              'target_asset':  LUNA.get_info().to_dict(),
                                                              'interval': 5,
                                                              'last_purchase': 0,
                                                              'dca_amount': '250000'}}

                                                   ]

    return mock


class TestDbSync(unittest.TestCase):

    def setUp(self):
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.settings.test import DB_URL as DB_URL_TEST
        from bot.db.database import create_database_objects
        from bot.util import read_artifact
        from bot.db_sync import Sync
        assert DB_URL == DB_URL_TEST, "invalid DB_URL={}".format(
            DB_URL)

        # drop_database_objects()
        create_database_objects()
        self.network = read_artifact("localterra")
        self.dca_contract = self.network["dcaAddress"]
        self.terra = LocalTerra()
        self.test1_wallet = self.terra.wallets["test1"]
        self.sync = Sync()
        self.sync.dca = mock_dca()

    def tearDown(self):
        os.environ['DCA_BOT'] = 'test'
        from bot.db.database import drop_database_objects
        drop_database_objects()

    def test_get_cfg_dca(self):
        self.assertEqual(self.sync.cfg_dca, {})
        res = self.sync.get_cfg_dca()
        self.assertNotEqual(self.sync.cfg_dca, {})
        expected_keys = ['max_hops', 'max_spread', 'whitelisted_fee_assets',
                         'whitelisted_tokens', 'factory_addr', 'router_addr']

        self.assertEqual(len(res.keys()), len(expected_keys))
        self.assertEqual(len(res.keys()), len(self.sync.cfg_dca.keys()))

        for k in self.sync.cfg_dca.keys():
            self.assertIn(k, expected_keys)

    def test_insert_user_into_db(self):
        users = self.sync.db.get_users()
        self.assertEqual(len(users), 0)

        self.sync.insert_user_into_db("user_address")

        users = self.sync.db.get_users()
        self.assertEqual(len(users), 1)

    def test_sync_user_tip_balance(self):
        from bot.db.table.user_tip_balance import UserTipBalance

        # setup test
        self.sync.insert_user_into_db(TEST_USER)

        # build tip_0
        denom_0 = "denom_0"
        amount_0 = 1000000
        asset_class_0 = "token"
        tip_0 = {'info': {asset_class_0: {
            'contract_addr': denom_0}}, 'amount': str(amount_0)}
        # build tip_1
        denom_1 = 'denom_1'
        amount_1 = 1000000
        asset_class_1 = "native_token"
        tip_1 = {'info': {asset_class_1: {
            'denom': denom_1}}, 'amount': str(amount_1)}

        # tips to sync
        tips = [tip_0, tip_1]
        self.sync._sync_user_tip_balance(TEST_USER, tips)

        # check entries in db are fine
        db_tips = self.sync.db.get_user_tip_balance(TEST_USER)
        self.assertEqual(len(db_tips), 2)

        self.assertEqual(db_tips[0].user_address, TEST_USER)
        self.assertEqual(db_tips[0].amount, amount_0)
        self.assertEqual(db_tips[0].denom, denom_0)
        self.assertEqual(db_tips[0].asset_class, asset_class_0)
        self.assertEqual(db_tips[0].id,
                         UserTipBalance.build_id(TEST_USER, denom_0))

        new_amount_0 = 10
        tip_0_new_amount = {'info': {asset_class_0: {
            'contract_addr': denom_0}}, 'amount': str(new_amount_0)}
        new_tips = [tip_0_new_amount]
        # tips to sync
        self.sync._sync_user_tip_balance(TEST_USER, new_tips)

        db_tips = self.sync.db.get_user_tip_balance(TEST_USER)
        self.assertEqual(len(db_tips), 1)

        self.assertEqual(db_tips[0].user_address, TEST_USER)  # same as before
        # this has changed
        self.assertEqual(db_tips[0].amount, new_amount_0)
        self.assertEqual(db_tips[0].denom, denom_0)  # same as before
        self.assertEqual(db_tips[0].asset_class,
                         asset_class_0)  # same as before
        self.assertEqual(db_tips[0].id,
                         UserTipBalance.build_id(TEST_USER, denom_0))  # same as before

    def test_sync_dca_oders(self):
        from bot.db.table.dca_order import DcaOrder
        # setup test
        max_spread = "0.1"
        max_hops = 3
        self.sync.insert_user_into_db(TEST_USER)

        # build order 1
        order_id_1 = 1
        initial_asset_denom_1 = "initial_asset_denom_1"
        initial_asset_asset_class_1 = "token"
        initial_asset_amount_1 = 1
        target_asset_denom_1 = "target_denom_1"
        target_asset_class_1 = "native_token"
        interval_1 = 1
        last_purchase_1 = 1
        dca_amount_1 = 1
        token_allowance_1 = 1

        order_1 = {"token_allowance": str(token_allowance_1),
                   "order": {'id': order_id_1,
                             'initial_asset': {'info': {initial_asset_asset_class_1: {'contract_addr': initial_asset_denom_1}}, 'amount': str(initial_asset_amount_1)},
                             'target_asset': {target_asset_class_1: {'denom': target_asset_denom_1}},
                             'interval': interval_1,
                             'last_purchase': last_purchase_1,
                             'dca_amount': str(dca_amount_1)}
                   }

        # build order 2
        order_id_2 = 2
        initial_asset_denom_2 = "initial_asset_denom_2"
        initial_asset_asset_class_2 = "token"
        initial_asset_amount_2 = 2
        target_asset_denom_2 = "target_denom_1"
        target_asset_class_2 = "native_token"
        interval_2 = 2
        last_purchase_2 = 2
        dca_amount_2 = 2
        token_allowance_2 = 2

        order_2 = {"token_allowance": str(token_allowance_2),
                   "order": {'id': order_id_2,
                             'initial_asset': {'info': {initial_asset_asset_class_2: {'contract_addr': initial_asset_denom_2}}, 'amount': str(initial_asset_amount_2)},
                             'target_asset': {target_asset_class_2: {'denom': target_asset_denom_2}},
                             'interval': interval_2,
                             'last_purchase': last_purchase_2,
                             'dca_amount': str(dca_amount_2)}}

        # orders to sync
        orders = [order_1, order_2]
        self.sync._sync_dca_oders(TEST_USER, max_spread, max_hops, orders)

        # check entries in db are fine
        user_orders = self.sync.db.get_dca_orders(user_address=TEST_USER)
        self.assertEqual(len(user_orders), 2)

        self.assertEqual(
            user_orders[0].id, DcaOrder.build_id(TEST_USER, order_id_1))
        self.assertEqual(
            user_orders[0].dca_order_id, order_id_1)
        self.assertEqual(
            user_orders[0].initial_asset_class, initial_asset_asset_class_1)
        self.assertEqual(
            user_orders[0].initial_asset_amount, initial_asset_amount_1)
        self.assertEqual(
            user_orders[0].initial_asset_denom, initial_asset_denom_1)
        self.assertEqual(
            user_orders[0].target_asset_class, target_asset_class_1)
        self.assertEqual(
            user_orders[0].target_asset_denom, target_asset_denom_1)
        self.assertEqual(
            user_orders[0].interval,  interval_1)
        self.assertEqual(
            user_orders[0].dca_amount, dca_amount_1)
        self.assertEqual(
            user_orders[0].user_address,  TEST_USER)
        self.assertEqual(
            user_orders[0].token_allowance, token_allowance_1)
        self.assertEqual(
            user_orders[0].last_purchase, last_purchase_1)
        self.assertEqual(
            user_orders[0].max_spread, max_spread)
        self.assertEqual(
            user_orders[0].max_hops, max_hops)
        self.assertEqual(
            user_orders[0].schedule, False)
        self.assertEqual(
            user_orders[0].next_run_time, None)

        new_initial_asset_denom_1 = "new_initial_asset_denom_1"
        new_initial_asset_amount_1 = 10
        new_order_1 = {"token_allowance": str(token_allowance_1),
                       "order": {'id': order_id_1,
                                 'initial_asset': {'info': {initial_asset_asset_class_1: {'contract_addr': new_initial_asset_denom_1}}, 'amount': str(new_initial_asset_amount_1)},
                                 'target_asset': {target_asset_class_1: {'denom': target_asset_denom_1}},
                                 'interval': interval_1,
                                 'last_purchase': last_purchase_1,
                                 'dca_amount': str(dca_amount_1)}
                       }
        # orders to sync
        orders = [new_order_1]
        self.sync._sync_dca_oders(TEST_USER, max_spread, max_hops, orders)

        # check entries in db are fine
        user_orders = self.sync.db.get_dca_orders(user_address=TEST_USER)
        self.assertEqual(len(user_orders), 1)

        self.assertEqual(
            user_orders[0].id, DcaOrder.build_id(TEST_USER, order_id_1))  # same as before
        self.assertEqual(
            user_orders[0].dca_order_id, order_id_1)  # same as before
        self.assertEqual(
            user_orders[0].initial_asset_class, initial_asset_asset_class_1)  # same as before
        # this has changed
        self.assertEqual(
            user_orders[0].initial_asset_amount, new_initial_asset_amount_1)
        # this has changed
        self.assertEqual(
            user_orders[0].initial_asset_denom, new_initial_asset_denom_1)
        self.assertEqual(
            user_orders[0].target_asset_class, target_asset_class_1)  # same as before
        self.assertEqual(
            user_orders[0].target_asset_denom, target_asset_denom_1)  # same as before
        self.assertEqual(
            user_orders[0].interval,  interval_1)  # same as before
        self.assertEqual(
            user_orders[0].dca_amount, dca_amount_1)  # same as before
        self.assertEqual(
            user_orders[0].user_address,  TEST_USER)  # same as before
        self.assertEqual(
            user_orders[0].token_allowance, token_allowance_1)  # same as before
        self.assertEqual(
            user_orders[0].last_purchase, last_purchase_1)  # same as before
        self.assertEqual(
            user_orders[0].max_spread, max_spread)  # same as before
        self.assertEqual(
            user_orders[0].max_hops, max_hops)  # same as before
        self.assertEqual(
            user_orders[0].schedule, False)  # same as before
        self.assertEqual(
            user_orders[0].next_run_time, None)  # same as before

    def test_sync_whitelisted_fee_asset(self):
        denom_1 = "denom_1"
        amount_1 = 1
        asset_class_1 = "token"
        asset_1 = {'info': {asset_class_1: {
            'contract_addr': denom_1}}, 'amount': str(amount_1)}

        denom_2 = "denom_2"
        amount_2 = 2
        asset_class_2 = "native_token"
        asset_2 = {'info': {asset_class_2: {'denom': denom_2}},
                   'amount': str(amount_2)}

        # fees to sync
        fees = [asset_1, asset_2]
        self.sync._sync_whitelisted_fee_asset(fees)

        # check entries in db are fine
        db_fees = self.sync.db.get_whitelisted_fee_asset()
        self.assertEqual(len(db_fees), 2)

        self.assertEqual(db_fees[0].amount, amount_1)
        self.assertEqual(db_fees[0].asset_class, asset_class_1)
        self.assertEqual(db_fees[0].denom,  denom_1)

        new_amount_1 = 10
        new_asset_1 = {
            'info': {asset_class_1: {'contract_addr': denom_1}}, 'amount': str(new_amount_1)}
        # fees to sync
        fees = [new_asset_1]
        self.sync._sync_whitelisted_fee_asset(fees)

        # check entries in db are fine
        db_fees = self.sync.db.get_whitelisted_fee_asset()
        self.assertEqual(len(db_fees), 1)

        # this has changes
        self.assertEqual(db_fees[0].amount, new_amount_1)
        self.assertEqual(db_fees[0].asset_class,
                         asset_class_1)  # same as before
        self.assertEqual(db_fees[0].denom,  denom_1)  # same as before

    def test_sync_whitelisted_token(self):
        # tokens to sync
        tokens = [TOKEN1.get_info().to_dict(), TOKEN2.get_info().to_dict()]
        self.sync._sync_whitelisted_token(tokens)

        # check entries in db are fine
        db_tokens = self.sync.db.get_whitelisted_tokens()
        self.assertEqual(len(db_tokens), 2)

        self.assertEqual(db_tokens[0].asset_class,
                         TOKEN1.get_info().asset_class.value)
        self.assertEqual(db_tokens[0].denom, TOKEN1.get_denom())

        new_token1 = TokenAsset("new_denom_1", "1000")

        # tokens to sync
        tokens = [new_token1.get_info().to_dict()]
        self.sync._sync_whitelisted_token(tokens)

        # check entries in db are fine
        db_tokens = self.sync.db.get_whitelisted_tokens()
        self.assertEqual(len(db_tokens), 1)

        self.assertEqual(db_tokens[0].asset_class,
                         new_token1.get_info().asset_class.value)
        self.assertEqual(db_tokens[0].denom, new_token1.get_denom())

    def test_sync_whitelisted_hop(self):

        # stored some token in the db
        tokens = [TOKEN1.get_info().to_dict(), TOKEN2.get_info().to_dict(),
                  TOKEN3.get_info().to_dict()]
        self.sync._sync_whitelisted_token(tokens)

        # sync hops
        self.sync.sync_whitelisted_hop()

        # check entries in db are fine
        db_hops = self.sync.db.get_whitelisted_hops()
        self.assertEqual(len(db_hops), 2)

        expected_pair_id = ["denom1-denom2", "denom2-denom3"]
        actual_pair_id = [str(h.pair_id) for h in db_hops]
        expected_pair_id.sort()
        actual_pair_id.sort()

        self.assertEqual(actual_pair_id, expected_pair_id)

        # sync again
        tokens = [TOKEN1.get_info().to_dict(), TOKEN2.get_info().to_dict()]
        self.sync._sync_whitelisted_token(tokens)

        # sync hops
        self.sync.sync_whitelisted_hop()

        # check entries in db are fine
        db_hops = self.sync.db.get_whitelisted_hops()
        self.assertEqual(len(db_hops), 1)

        expected_pair_id = ["denom1-denom2"]
        actual_pair_id = [str(h.pair_id) for h in db_hops]
        self.assertEqual(actual_pair_id, expected_pair_id)

    def test_sync_user_data(self):
        # setup test
        self.sync.insert_user_into_db(TEST_USER)

        orders = self.sync.db.get_dca_orders(id=None, user_address=TEST_USER)
        self.assertEqual(len(orders), 0)

        self.sync.sync_user_data(TEST_USER)

        orders = self.sync.db.get_dca_orders(id=None, user_address=TEST_USER)
        self.assertEqual(len(orders), 2)

    def test_sync_dca_cfg(self):
        # setup test

        # check whitelisted tables are empty
        db_tokens = self.sync.db.get_whitelisted_tokens()
        self.assertEqual(len(db_tokens), 0)

        db_fees = self.sync.db.get_whitelisted_fee_asset()
        self.assertEqual(len(db_fees), 0)

        db_hops = self.sync.db.get_whitelisted_hops()
        self.assertEqual(len(db_hops), 0)

        db_hops_all = self.sync.db.get_whitelisted_hops_all()
        self.assertEqual(len(db_hops_all), 0)

        # sync configuration
        self.sync.sync_dca_cfg()

        # check entries in db are fine
        db_token = self.sync.db.get_whitelisted_tokens()
        self.assertEqual(len(db_token), 4)

        self.assertEqual(db_token[0].asset_class, "token")
        self.assertEqual(db_token[0].denom, "denom1")

        db_fees = self.sync.db.get_whitelisted_fee_asset()
        self.assertEqual(len(db_fees), 2)

        self.assertEqual(db_fees[1].asset_class, "native_token")
        self.assertEqual(db_fees[1].denom, "uluna")

        db_hops = self.sync.db.get_whitelisted_hops()
        self.assertEqual(len(db_hops), 3)

        self.assertEqual(db_hops[0].pair_id, "denom1-denom2")
        self.assertEqual(db_hops[1].pair_id, "denom2-denom3")
        self.assertEqual(db_hops[2].pair_id, "denom3-uluna")

        db_hops_all = self.sync.db.get_whitelisted_hops_all()
        self.assertEqual(len(db_hops_all), 11)
        actual_hops = [h["hops"] for h in db_hops_all]
        expected_hops = ["<1>",
                         "<2>",
                         "<3>",
                         "<inverse-1>",
                         "<inverse-2>",
                         "<inverse-3>",
                         "<1><2>",
                         "<2><inverse-3>",
                         "<3><inverse-2>",
                         "<inverse-2><inverse-1>",
                         "<1><2><inverse-3>"
                         ]

        self.assertEqual(actual_hops, expected_hops)

    def test_fill_token_price_table(self):
        list_tp = self.sync.db.get_token_price()
        self.assertEqual(len(list_tp), 0)

        self.sync.fill_token_price_table()

        list_tp = self.sync.db.get_token_price()
        self.assertEqual(len(list_tp), 4)

    def test_sync_token_price(self):
        self.sync.fill_token_price_table()
        list_tp = self.sync.db.get_token_price()
        self.assertEqual(len(list_tp), 4)

        for tp in list_tp:
            self.assertIsNone(tp.price)

        self.sync.sync_token_price()

        list_tp = self.sync.db.get_token_price()
        self.assertEqual(len(list_tp), 4)
        for tp in list_tp:
            self.assertIsNotNone(tp.price)


def get_test_names():
    testNames = [
        "test_get_cfg_dca",
        "test_insert_user_into_db",
        "test_sync_user_tip_balance",
        "test_sync_dca_oders",
        "test_sync_whitelisted_fee_asset",
        "test_sync_whitelisted_token",
        "test_sync_whitelisted_hop",
        "test_sync_user_data",
        "test_sync_dca_cfg",
        "test_fill_token_price_table",
        "test_sync_token_price"

    ]
    testFullNames = [
        "test_db_sync.TestDbSync.{}".format(t) for t in testNames]
    return testFullNames


if __name__ == '__main__':
    testFullNames = get_test_names()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
