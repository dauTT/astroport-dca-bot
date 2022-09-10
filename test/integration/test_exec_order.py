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


class TestExecOrder(unittest.TestCase):

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
        pass


if __name__ == '__main__':
    testNames = [
        "xxx"
    ]

    testFullNames = [
        "test_exec_order.TestExecOrder.{}".format(t) for t in testNames]

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(testFullNames)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

    pass
