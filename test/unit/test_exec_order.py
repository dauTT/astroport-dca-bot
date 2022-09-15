
import unittest
import os
from unittest.mock import Mock
from terra_sdk.client.localterra import LocalTerra
from bot.type import NativeAsset, TokenAsset


TOKEN1 = TokenAsset("denom1", "1000")
TOKEN2 = TokenAsset("denom2", "2000")
TOKEN3 = TokenAsset("denom3", "3000")
TOKEN4 = TokenAsset("denom4", "4000")
LUNA = NativeAsset("uluna", "5000")

TEST_USER = "user_123"

# all hops between denom1 and denom3
LIST_HOPS_STRING = ['<3>', '<1><2>', '<3><inverse-2>', '<1><2><inverse-3>']
TOKEN_RECEIVE = [2000, 1000, 4000, 3000]
TOKEN_RECEIVE_MAP = dict(zip(LIST_HOPS_STRING, TOKEN_RECEIVE))


def mock_responses(responses, default_response=None):
    return lambda input: responses[input] if input in responses else default_response


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

            {'asset_infos': [TOKEN1.get_info().to_dict(), TOKEN3.get_info().to_dict()],
                'contract_addr': 'contract_addr4',
                'liquidity_token': 'liquidity_token4',
                'pair_type': {'xyk': {}}}]

    }

    mock.query_get_user_config.return_value = {
        'last_id': 1,
        'max_hops': None,
        'max_spread': None,
        'tip_balance': [TOKEN1.get_asset(), NativeAsset("uluna", "15000").get_asset()]

    }

    mock.simulate_swap_operations.side_effect = TOKEN_RECEIVE

    return mock


class TestExecOrder(unittest.TestCase):

    def setUp(self):
        os.environ['DCA_BOT'] = 'test'
        from bot.settings import DB_URL
        from bot.settings.test import DB_URL as DB_URL_TEST
        from bot.db.database import create_database_objects
        from bot.util import read_artifact
        from bot.exec_order import ExecOrder
        assert DB_URL == DB_URL_TEST, "invalid DB_URL={}".format(
            DB_URL)

        # drop_database_objects()
        create_database_objects()
        self.network = read_artifact("localterra")
        self.dca_contract = self.network["dcaAddress"]
        self.terra = LocalTerra()
        self.test1_wallet = self.terra.wallets["test1"]
        self.eo = ExecOrder()
        self.eo.dca = mock_dca()
        # sync configuration
        self.eo.sync_dca_cfg()

        self.eo.insert_user_into_db(TEST_USER)

    def tearDown(self):
        os.environ['DCA_BOT'] = 'test'
        from bot.db.database import drop_database_objects
        drop_database_objects()

    def test_build_fee_redeem(self):
        # setup test
        from bot.db.table.user_tip_balance import UserTipBalance

        tip1 = UserTipBalance(TEST_USER, TOKEN1)
        tip2 = UserTipBalance(TEST_USER, LUNA)

        self.eo.db.insert_or_update(tip1)
        self.eo.db.insert_or_update(tip2)

        db_tips = self.eo.db.get_user_tip_balance(TEST_USER)
        self.assertEqual(len(db_tips), 2)

        db_fees = self.eo.db.get_whitelisted_fee_asset()
        self.assertEqual(len(db_fees), 2)

        fees = self.eo.build_fee_redeem(TEST_USER, 1)
        self.assertEqual([f.get_asset() for f in fees], [
            TOKEN1.get_asset()])

        fees = self.eo.build_fee_redeem(TEST_USER, 2)
        self.assertEqual([f.get_asset() for f in fees], [
            TOKEN1.get_asset(), LUNA.get_asset()])

        with self.assertRaises(AssertionError):
            self.eo.build_fee_redeem(TEST_USER, 3)

    def test_choose_best_execution_hop1(self):
        from bot.db.table.token_price import TokenPrice
        from bot.db.table.user_tip_balance import UserTipBalance

        # setup tip user tip
        tip1 = UserTipBalance(TEST_USER, TokenAsset("denom1", "2000"))
        tip2 = UserTipBalance(TEST_USER, LUNA)
        self.eo.db.insert_or_update(tip1)
        self.eo.db.insert_or_update(tip2)

        # setup token price
        tp1 = TokenPrice("denom1", "id_1", "symbol1", 1000000, 100)
        tp2 = TokenPrice("denom2", "id_2", "symbol2", 1000000, 200)
        tp3 = TokenPrice("denom3", "id_3", "symbol3", 1000000, 300)
        tp4 = TokenPrice("uluna", "luna-2", "luna", 1000000, 400)

        self.eo.db.insert_or_update(tp1)
        self.eo.db.insert_or_update(tp2)
        self.eo.db.insert_or_update(tp3)
        self.eo.db.insert_or_update(tp4)

        prices = self.eo.get_token_price_map()

        self.assertEqual(prices["denom1"], 0.0001)
        self.assertEqual(prices["denom2"], 0.0002)
        self.assertEqual(prices["denom3"], 0.0003)
        self.assertEqual(prices["uluna"], 0.0004)

        # get hops with start_denom=denom1 and target_denom=denom3
        hops_info = self. eo.db.get_whitelisted_hops_all("denom1", "denom3")
        list_hops = [h["hops"] for h in hops_info]
        self.assertEqual(list_hops, LIST_HOPS_STRING)

        fee_reedem_usd = self.eo.build_fee_reedem_usd_map(
            TEST_USER, LIST_HOPS_STRING, prices)

        # the user has sufficient fees to pay any hops in LIST_HOPS_STRING
        self.assertEqual(len(fee_reedem_usd.keys()), len(LIST_HOPS_STRING))

        # 1000 * 0.0001
        self.assertAlmostEqual(fee_reedem_usd["<3>"], 0.1)
        # (1000 * 0.0001 + 1000 * 0.0001)
        self.assertAlmostEqual(fee_reedem_usd["<1><2>"], 0.2)
        # (1000 * 0.0001 + 1000 * 0.0001)
        self.assertAlmostEqual(fee_reedem_usd["<3><inverse-2>"], 0.2)
        # (1000 * 0.0001 + 1000 * 0.0001 + 5000 * 0.0004)
        self.assertAlmostEqual(fee_reedem_usd["<1><2><inverse-3>"], 2.2)

        execution = {}
        for hop in TOKEN_RECEIVE_MAP:
            execution[hop] = TOKEN_RECEIVE_MAP[hop] * \
                prices["denom3"] - fee_reedem_usd[hop]

        # 2000 * 0.0003 - 0.1 = 0.6 - 0.1 = 0.5
        self.assertAlmostEqual(execution['<3>'], 0.5)
        # 1000 * 0.0003 - 0.2 = 0.3 - 0.2 =  0.1
        self.assertAlmostEqual(execution['<1><2>'], 0.1)
        # 4000 * 0.0003 - 0.2 = 1.2 - 0.2 = 1
        self.assertAlmostEqual(execution['<3><inverse-2>'], 1)
        # 3000 * 0.0003 - 2.2 = 0.9 - 2.2 = -1.3
        self.assertAlmostEqual(
            execution['<1><2><inverse-3>'], -1.3)
        best_hop = self.eo.choose_best_execution_hop(
            "denom3", 1000, fee_reedem_usd, prices)

        self.assertEqual(best_hop, "<3><inverse-2>")

    def test_choose_best_execution_hop2(self):
        from bot.db.table.token_price import TokenPrice
        from bot.db.table.user_tip_balance import UserTipBalance

        # setup tip user
        tip1 = UserTipBalance(TEST_USER, TokenAsset("denom1", "1000"))
        tip2 = UserTipBalance(TEST_USER, LUNA)
        self.eo.db.insert_or_update(tip1)
        self.eo.db.insert_or_update(tip2)

        # setup token price
        tp1 = TokenPrice("denom1", "id_1", "symbol1", 1000000, 100)
        tp2 = TokenPrice("denom2", "id_2", "symbol2", 1000000, 200)
        tp3 = TokenPrice("denom3", "id_3", "symbol3", 1000000, 300)
        tp4 = TokenPrice("uluna", "luna-2", "luna", 1000000, 800)

        self.eo.db.insert_or_update(tp1)
        self.eo.db.insert_or_update(tp2)
        self.eo.db.insert_or_update(tp3)
        self.eo.db.insert_or_update(tp4)

        prices = self.eo.get_token_price_map()

        self.assertEqual(prices["denom1"], 0.0001)
        self.assertEqual(prices["denom2"], 0.0002)
        self.assertEqual(prices["denom3"], 0.0003)
        self.assertEqual(prices["uluna"], 0.0008)

        # get hops with start_denom=denom1 and target_denom=denom3
        hops_info = self. eo.db.get_whitelisted_hops_all("denom1", "denom3")
        list_hops = [h["hops"] for h in hops_info]
        self.assertEqual(list_hops, LIST_HOPS_STRING)

        fee_reedem_usd = self.eo.build_fee_reedem_usd_map(
            TEST_USER, LIST_HOPS_STRING, prices)

        # The bot could not construct the fee_redem for the hops = '<1><2><inverse-3>'
        # because the user does not have sufficient fees to pay.
        self.assertEqual(len(fee_reedem_usd.keys()), len(LIST_HOPS_STRING)-1)
        self.assertEqual(list(fee_reedem_usd.keys()), [
                         '<3>', '<1><2>', '<3><inverse-2>'])

        # (1000 * 0.0001)
        self.assertAlmostEqual(fee_reedem_usd["<3>"], 0.1)
        # (1000 * 0.0001 + 5000 * 0.0008)
        self.assertAlmostEqual(fee_reedem_usd["<1><2>"],  4.1)
        # (1000 * 0.0001 + 5000 * 0.0008)
        self.assertAlmostEqual(fee_reedem_usd["<3><inverse-2>"], 4.1)

        execution = {}
        for hop in fee_reedem_usd:
            execution[hop] = TOKEN_RECEIVE_MAP[hop] * \
                prices["denom3"] - fee_reedem_usd[hop]

        # 2000 * 0.0003 - 0.1 = 0.6 - 0.1 = 0.5
        self.assertAlmostEqual(execution['<3>'], 0.5)
        # 1000 * 0.0003 - 4.1 = 0.3 - 4.1 = 0.195
        self.assertAlmostEqual(execution['<1><2>'],  -3.8)
        # 4000 * 0.0003 - 4.1 = 1.2 - 4.1 = 1.095
        self.assertAlmostEqual(execution['<3><inverse-2>'], -2.9)

        best_hop = self.eo.choose_best_execution_hop(
            "denom3", 1000, fee_reedem_usd, prices)

        self.assertEqual(best_hop, "<3>")

    def test_build_hops(self):
        pass


def get_test_names():
    testNames = [
        "test_build_fee_redeem",
        "test_choose_best_execution_hop1",
        "test_choose_best_execution_hop2"
    ]
    testFullNames = [
        "test_exec_order.TestExecOrder.{}".format(t) for t in testNames]
    return testFullNames


if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.DEBUG)
    testFullNames = get_test_names()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
