
from terra_sdk.client.localterra import LocalTerra
from bot.type import TokenAsset, NativeAsset
from bot.util import read_artifact, write_artifact
from bot.dca import DCA
import logging

logger = logging.getLogger(__name__)

DCA_BINARY_PATH = "test/integration/artifacts/astroport_dca_module.wasm"

NETWORK = read_artifact("localterra")

INSTANTIATE_MSG = {
    "factory_addr": NETWORK["factoryAddress"],
    "max_hops": 3,
    "max_spread": "0.5",
    "per_hop_fee": "100000",
    "router_addr": NETWORK["routerAddress"],
    "whitelisted_tokens": [
        TokenAsset(NETWORK["tokenAddresses"]
                   ["AAA"]).get_info().to_dict(),
        TokenAsset(NETWORK["tokenAddresses"]
                   ["BBB"]).get_info().to_dict(),
        TokenAsset(NETWORK["tokenAddresses"]
                   ["CCC"]).get_info().to_dict(),
        TokenAsset(NETWORK["tokenAddresses"]
                   ["DDD"]).get_info().to_dict(),
        NativeAsset("uluna").get_info().to_dict(),
    ],
    "whitelisted_fee_assets": [
        TokenAsset(NETWORK["tokenAddresses"]
                   ["CCC"], "1000").get_asset(),
        TokenAsset(NETWORK["tokenAddresses"]
                   ["AAA"], "2000").get_asset(),
        NativeAsset("uluna", "3000").get_asset(),
    ]
}


class Setup:

    def __init__(self):
        self.terra = LocalTerra()
        self.network = NETWORK
        self.dca1 = DCA(self.terra, self.terra.wallets["test1"])
        self.dca2 = DCA(self.terra, self.terra.wallets["test2"])
        self.dca3 = DCA(self.terra, self.terra.wallets["test3"])

    def upload_dca_contract(self) -> str:
        code_id = self.dca1.upload_contract(
            DCA_BINARY_PATH)
        self.network["dcaCodeId"] = code_id
        write_artifact(self.network, "localterra")
        return code_id

    def instantiate_dca_contract(self, dca_code_id: int):
        contract_address = self.dca1.instantiate(
            dca_code_id, INSTANTIATE_MSG)

        self.network["dcaAddress"] = contract_address
        write_artifact(self.network, "localterra")
        print("dca contract_address=", contract_address)

    def deploy_dca_contract(self):
        code_id = self.upload_dca_contract()
        self.instantiate_dca_contract(int(code_id))

    def get_block_time_second(self) -> int:
        from dateutil.parser import parse
        time_string = self.terra.tendermint.block_info()[
            'block']['header']['time']
        date_time = parse(time_string)
        return round(date_time.timestamp())

    def create_test_orders(self):
        self.dca1.set_dca_addr(self.network["dcaAddress"])
        self.dca2.set_dca_addr(self.network["dcaAddress"])
        self.dca3.set_dca_addr(self.network["dcaAddress"])
        # create 2 orders for test1 account
        self.dca1.execute_create_oder(
            TokenAsset(self.network["tokenAddresses"]["AAA"], "1000000"),
            NativeAsset("uluna").get_info(),
            10, 10000, None)

        self.dca1.execute_create_oder(
            TokenAsset(self.network["tokenAddresses"]["AAA"], "1000000"),
            TokenAsset(self.network["tokenAddresses"]["CCC"]).get_info(),
            10, 10000, self.get_block_time_second()+10)

        # create 1 orders for test2 account
        self.dca2 = DCA(
            self.terra, self.terra.wallets["test2"], self.network["dcaAddress"])
        self.dca2.execute_create_oder(
            TokenAsset(self.network["tokenAddresses"]["AAA"], "1000000"),
            NativeAsset("uluna").get_info(),
            5, 250000, None)

        # create 1 order for test3 account
        self.dca3 = DCA(
            self.terra, self.terra.wallets["test3"], self.network["dcaAddress"])
        self.dca3.execute_create_oder(
            TokenAsset(self.network["tokenAddresses"]["AAA"], "1000000"),
            TokenAsset(self.network["tokenAddresses"]["CCC"]).get_info(),
            10, 500000, self.get_block_time_second()+10)

    def add_users_tip_balance(self):
        self.dca1.set_dca_addr(self.network["dcaAddress"])
        self.dca2.set_dca_addr(self.network["dcaAddress"])
        self.dca3.set_dca_addr(self.network["dcaAddress"])

        asset1 = TokenAsset(self.network["tokenAddresses"]["CCC"], "1000000")
        asset2 = NativeAsset("uluna", "1000000")
        self.dca1.execute_add_bot_tip([asset1, asset2])
        self.dca2.execute_add_bot_tip([asset1, asset2])
        self.dca3.execute_add_bot_tip([asset1, asset2])

    def run(self):
        self.deploy_dca_contract()
        self.create_test_orders()
        self.add_users_tip_balance()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    s = Setup()
    s.run()
