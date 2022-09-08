import unittest
import os
from bot.type import AssetClass, NativeAsset, TokenAsset, AssetInfo, \
    Asset, AstroSwap
from bot.util import read_artifact
from test.integration.setup import DCA_BINARY_PATH, INSTANTIATE_MSG
from terra_sdk.client.localterra import LocalTerra
from terra_sdk.core import AccAddress, Coins
from terra_sdk.exceptions import LCDResponseError
from typing import List


class TestDca(unittest.TestCase):

    def setUp(self):
        os.environ['DCA_BOT'] = 'dev'
        from bot.settings import DB_URL
        from bot.settings.dev import DB_URL as DB_URL_DEV
        from bot.dca import DCA
        assert DB_URL == DB_URL_DEV, "invalid DB_URL={}".format(
            DB_URL)

        self.network = read_artifact("localterra")
        self.dca_contract = self.network["dcaAddress"]
        self.terra = LocalTerra()

        # To make the tests as much independent as possible we use 3 users.
        # However the execute tests can be run only once because they modified the
        # blockchain state. They will fail if we run them a second time without resetting the
        # state of of the blockchain.
        self.test1_wallet = self.terra.wallets["test1"]
        self.test2_wallet = self.terra.wallets["test2"]
        self.test3_wallet = self.terra.wallets["test3"]
        self.dca1 = DCA(self.terra, self.test1_wallet, self.dca_contract)
        self.dca2 = DCA(self.terra, self.test2_wallet, self.dca_contract)
        self.dca3 = DCA(self.terra, self.test3_wallet, self.dca_contract)

    # @unittest.skip("skip test_query_get_config")
    def test_query_get_config(self):
        res = self.dca2.query_get_config()

        expected_result = {'max_hops': 3,
                           'max_spread': '0.5',
                           'whitelisted_fee_assets': [{'info': {'token': {'contract_addr': 'terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul'}}, 'amount': '1000'},
                                                      {'info': {'token': {
                                                          'contract_addr': 'terra1cyd63pk2wuvjkqmhlvp9884z4h89rqtn8w8xgz9m28hjd2kzj2cq076xfe'}}, 'amount': '2000'},
                                                      {'info': {'native_token': {'denom': 'uluna'}}, 'amount': '3000'}],
                           'whitelisted_tokens': [{'token': {'contract_addr': 'terra1cyd63pk2wuvjkqmhlvp9884z4h89rqtn8w8xgz9m28hjd2kzj2cq076xfe'}},
                                                  {'token': {
                                                      'contract_addr': 'terra14haqsatfqxh3jgzn6u7ggnece4vhv0nt8a8ml4rg29mln9hdjfdq9xpv0p'}},
                                                  {'token': {
                                                      'contract_addr': 'terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul'}},
                                                  {'token': {
                                                      'contract_addr': 'terra10v0hrjvwwlqwvk2yhwagm9m9h385spxa4s54f4aekhap0lxyekys4jh3s4'}},
                                                  {'native_token': {'denom': 'uluna'}}],
                           'factory_addr': 'terra1qnmggqv3u03axw69cn578hukqhl4f2ze2k403ykcdlhj98978u7stv7fyj',
                           'router_addr': 'terra15kwtyl2jtf8frwh3zu2jntqvem8u36y8aw6yy9z3ypgkfjx6ct2q73xas8'}

        self.assertEqual(res['max_hops'], expected_result['max_hops'])
        self.assertEqual(res['max_spread'], expected_result['max_spread'])
        self.assertEqual(res['whitelisted_fee_assets'],
                         expected_result['whitelisted_fee_assets'])
        self.assertEqual(res['whitelisted_tokens'],
                         expected_result['whitelisted_tokens'])
        self.assertEqual(res['factory_addr'], expected_result['factory_addr'])
        self.assertEqual(res['router_addr'], expected_result['router_addr'])

    # @unittest.skip("skip test_query_get_user_config")
    def test_query_get_user_config(self):
        expected = {'last_id': 1,
                    'max_hops': None,
                    'max_spread': None,
                    'tip_balance': [{'info': {'token': {
                        'contract_addr': 'terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul'}}, 'amount': '1000000'},
                        {'info': {'native_token': {'denom': 'uluna'}}, 'amount': '1000000'}]}

        output = self.dca2.query_get_user_config(
            self.test2_wallet.key.acc_address)

        self.assertEqual(output["last_id"], expected["last_id"])
        self.assertEqual(output["max_hops"], expected["max_hops"])
        self.assertEqual(output["max_spread"], expected["max_spread"])
        self.assertEqual(output["tip_balance"], expected["tip_balance"])

    # @unittest.skip("skip test_query_get_user_dca_orders")
    def test_query_get_user_dca_orders(self):
        expected = [{'token_allowance': '1000000',
                    'order': {'id': 1,
                              'initial_asset': {'info': {'token': {'contract_addr': 'terra1cyd63pk2wuvjkqmhlvp9884z4h89rqtn8w8xgz9m28hjd2kzj2cq076xfe'}}, 'amount': '1000000'},
                              'target_asset': {'native_token': {'denom': 'uluna'}},
                              'interval': 5,
                              'last_purchase': 0,
                              'dca_amount': '250000'}}]

        output = self.dca2.query_get_user_dca_orders(
            self.test2_wallet.key.acc_address)

        self.assertEqual(len(output), len(expected))

        self.assertEqual(output[0]["token_allowance"],
                         expected[0]["token_allowance"])
        self.assertEqual(output[0]["order"]["id"],
                         expected[0]["order"]["id"])
        self.assertEqual(output[0]["order"]["initial_asset"],
                         expected[0]["order"]["initial_asset"])
        self.assertEqual(output[0]["order"]["target_asset"],
                         expected[0]["order"]["target_asset"])
        self.assertEqual(output[0]["order"]["interval"],
                         expected[0]["order"]["interval"])
        self.assertEqual(output[0]["order"]["last_purchase"],
                         expected[0]["order"]["last_purchase"])
        self.assertEqual(output[0]["order"]["dca_amount"],
                         expected[0]["order"]["dca_amount"])

    # @unittest.skip("skip test_get_astro_pools")
    def test_get_astro_pools(self):
        output = self.dca2.get_astro_pools()
        self.assertEqual(len(output["pairs"]), 4)

    # The test may fail due to timeout issue. Nonetheless most of the time
    # the upload did actually happened even if we get a timeout issue.
    # @unittest.skip("skip test_upload_contract")
    def test_upload_contract(self):
        """ test2 user is uploading the dca contract
        """

        # we have already uploaded the dca contract in the image dautt/astroport:v1.2.0
        # the code_id of the dca contract is 31
        code = self.terra.wasm.code_info(31)

        expected_dca_hash = '1BD6EDE6A2BCC2F921AA9FC9123CBBD15861C0E68F40B7F8EB8584B81BC64B8B'
        self.assertEqual(code["data_hash"], expected_dca_hash)

        # it will raise an error message because the code_id=32 does not exist yet
        with self.assertRaises(LCDResponseError):
            self.terra.wasm.code_info(32)

        # try to upload again the dca contract
        code_id = self.dca2.upload_contract(DCA_BINARY_PATH)
        self.assertEqual(code_id, "32")

        # Check that the hash is the same as in code 31
        code = self.terra.wasm.code_info(32)
        self.assertEqual(code["data_hash"], expected_dca_hash)

    # @unittest.skip("skip test_instantiate")
    def test_instantiate(self):
        """ test2 user is instantiating a new contract
        """
        # we have already uploaded the dca contract in the image dautt/astroport:v1.2.0
        # the code_id of the dca contract is 31
        contract_addr = self.dca2.instantiate(31, INSTANTIATE_MSG)
        self.assertRegex(contract_addr, "terra*")

    # @unittest.skip("skip test_execute_update_user_config")
    def test_execute_update_user_config(self):
        """ test3 user is updating its configuration
        """

        res = self.dca3.query_get_user_config(
            self.test3_wallet.key.acc_address)

        self.assertEqual(res['max_hops'], None)
        self.assertEqual(res['max_spread'], None)

        new_max_hops = 3
        new_max_spread = "0.4"
        self.dca3.execute_update_user_config(new_max_hops, new_max_spread)

        res = self.dca3.query_get_user_config(
            self.test3_wallet.key.acc_address)
        self.assertEqual(res['max_hops'], new_max_hops)
        self.assertEqual(res['max_spread'], new_max_spread)

    @unittest.skip("skip test_execute_update_config")
    def test_execute_update_config(self):
        # The execution of the method execute_update_config will throw following error msg:
        #       astroport::factory::ConfigResponse: missing field `is_generator_disabled`

        # There reason is that the dca contract (https://github.com/kaimen-sano/astroport-dca-mirror/tree/master/contracts/dca/src/handlers)
        # was developped under the latest main branch of astroport factory contract.
        # The one (with commit=c216ecd4f350113316be44d06a95569f451ac681) used in this image dautt/astroport:v1.2.0 is a little bit outdated
        self.dca1.execute_update_config(4, "0.6")

    # @unittest.skip("skip test_execute_add_bot_tip")
    def test_execute_add_bot_tip(self):
        """ test3 user is adding a tip
        """

        cfg_before = self.dca3.query_get_user_config(
            self.test3_wallet.key.acc_address)
        self.assertEqual(cfg_before["tip_balance"],
                         [{'info': {'token': {'contract_addr': 'terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul'}}, 'amount': '1000000'},
                          {'info': {'native_token': {'denom': 'uluna'}}, 'amount': '1000000'}])

        assets: List[Asset] = [NativeAsset("uluna", "1000000"),
                               # TODO: fix dca contract (https://github.com/kaimen-sano/astroport-dca-mirror/blob/master/contracts/dca/src/handlers/add_bot_tip.rs#L68)
                               # for the following two cases:
                               # 1) Adding the same tip asset again is not working!
                               # TokenAsset(self.network["tokenAddresses"]["CCC"], "1000000"),

                               # 2) Adding tip asset which is already configured as initial asset of an order is not working!
                               # TokenAsset(self.network["tokenAddresses"]["AAA"], "100000")
                               ]
        self.dca3.execute_add_bot_tip(assets)

        cfg_after = self.dca3.query_get_user_config(
            self.test3_wallet.key.acc_address)
        self.assertEqual(cfg_after["tip_balance"],
                         [{'info': {'token': {'contract_addr': 'terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul'}}, 'amount': '1000000'},
                          {'info': {'native_token': {'denom': 'uluna'}}, 'amount': '2000000'}])

    # @unittest.skip("skip test_execute_create_oder")
    def test_execute_create_oder(self):
        """ test1 user is creating one more order
        """

        orders = self.dca1.query_get_user_dca_orders(
            self.test1_wallet.key.acc_address)
        self.assertEqual(len(orders), 2)

        for i in [0, 1]:
            self.assertEqual(orders[i]['token_allowance'], "2000000")
            self.assertEqual(orders[i]['order']["initial_asset"]["info"]["token"]
                             ["contract_addr"], self.network["tokenAddresses"]["AAA"])

        self.dca1.execute_create_oder(
            TokenAsset(self.network["tokenAddresses"]["AAA"], "1000000"),
            TokenAsset(self.network["tokenAddresses"]["CCC"]).get_info(),
            10, 10000, 1000000)

        new_orders = self.dca1.query_get_user_dca_orders(
            self.test1_wallet.key.acc_address)
        self.assertEqual(len(new_orders), 3)

        expected = {'token_allowance': '3000000',
                    'order': {'id': 3,
                              'initial_asset': {'info': {'token': {'contract_addr': 'terra1cyd63pk2wuvjkqmhlvp9884z4h89rqtn8w8xgz9m28hjd2kzj2cq076xfe'}},
                                                'amount': '1000000'},
                              'target_asset': {'token': {'contract_addr': 'terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul'}},
                              'interval': 10,
                              'last_purchase': 1000000,
                              'dca_amount': '10000'}}

        for i in [0, 1, 2]:
            self.assertEqual(new_orders[i]['token_allowance'], "3000000")
            self.assertEqual(new_orders[i]['order']["initial_asset"]["info"]["token"]["contract_addr"],
                             self.network["tokenAddresses"]["AAA"])

        self.assertEqual(new_orders[2]['order']['id'], expected['order']['id'])
        self.assertEqual(
            new_orders[2]['order']['initial_asset'], expected['order']['initial_asset'])
        self.assertEqual(
            new_orders[2]['order']['target_asset'], expected['order']['target_asset'])
        self.assertEqual(new_orders[2]['order']
                         ['interval'], expected['order']['interval'])
        self.assertEqual(
            new_orders[2]['order']['last_purchase'], expected['order']['last_purchase'])
        self.assertEqual(
            new_orders[2]['order']['dca_amount'], expected['order']['dca_amount'])

    # @unittest.skip("skip test_execute_perform_dca_purchase")
    def test_execute_perform_dca_purchase(self):
        """ test2 user is executing a purchase for test1 user1
        """

        test1_addr = self.test1_wallet.key.acc_address
        token_CCC = AssetInfo(AssetClass.TOKEN,
                              self.network["tokenAddresses"]["CCC"])

        # Check token_CCC balance of the user before purchase
        balance = self.terra.wasm.contract_query(token_CCC.denom,
                                                 {"balance": {
                                                     "address": test1_addr}}
                                                 )

        amount_before = balance["balance"]

        # check order id = 1 to execute
        res = self.dca2.query_get_user_dca_orders(test1_addr)
        order_2 = res[1]

        self.assertEqual(order_2["order"]["id"], 2)
        self.assertEqual(order_2["order"]["initial_asset"]["info"]["token"]
                         ["contract_addr"], self.network["tokenAddresses"]["AAA"])
        self.assertEqual(order_2["order"]["initial_asset"]
                         ["amount"], "1000000")
        self.assertEqual(order_2["order"]["dca_amount"], "10000")
        self.assertEqual(order_2["order"]["target_asset"]
                         ["token"]["contract_addr"], self.network["tokenAddresses"]["CCC"])

        # prepare inputs
        id = 2

        fee_reedem: List[Asset] = [NativeAsset("uluna", "9000")]
        token_AAA = AssetInfo(AssetClass.TOKEN,
                              self.network["tokenAddresses"]["AAA"])
        token_BBB = AssetInfo(AssetClass.TOKEN,
                              self.network["tokenAddresses"]["BBB"])
        luna = AssetInfo(AssetClass.NATIVE_TOKEN, 'uluna')

        hops = [AstroSwap(token_AAA, token_BBB),
                AstroSwap(token_BBB, luna),
                AstroSwap(luna, token_CCC)
                ]
        # execute purchase
        self.dca2.execute_perform_dca_purchase(
            test1_addr, id, hops, fee_reedem)

        # Check token_CCC balance after purchase
        balance = self.terra.wasm.contract_query(token_CCC.denom,
                                                 {"balance": {
                                                     "address": test1_addr}}
                                                 )

        amount_after = balance["balance"]
        self.assertGreater(amount_after, amount_before)

        # check order id = 2 after purchase
        res = self.dca2.query_get_user_dca_orders(test1_addr)
        order_2 = res[1]

        self.assertEqual(order_2["order"]["id"], 2)
        self.assertEqual(order_2["order"]["initial_asset"]
                         ["amount"], "990000")


if __name__ == '__main__':
    testNames = [
        "test_dca.TestDca.test_query_get_config",
        "test_dca.TestDca.test_query_get_user_config",
        "test_dca.TestDca.test_query_get_user_dca_orders",
        "test_dca.TestDca.test_get_astro_pools",
        "test_dca.TestDca.test_upload_contract",
        "test_dca.TestDca.test_instantiate",
        "test_dca.TestDca.test_execute_update_user_config",
        "test_dca.TestDca.test_execute_add_bot_tip",
        "test_dca.TestDca.test_execute_create_oder",
        "test_dca.TestDca.test_execute_perform_dca_purchase",

    ]
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
