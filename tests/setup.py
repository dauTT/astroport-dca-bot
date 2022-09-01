
from terra_sdk.client.localterra import LocalTerra
from bot.type import TokenAsset, NativeAsset
from bot.util import read_artifact, write_artifact
from bot.dca import DCA
import logging

logger = logging.getLogger(__name__)


class Setup:

    def __init__(self):
        self.terra = LocalTerra()
        self.wallet = self.terra.wallets["test1"]
        self.network = read_artifact("localterra")

    def upload_dca_contract(self) -> str:
        code_id = DCA(self.terra, self.wallet).upload_contract(
            "tests/artifacts/astroport_dca_module.wasm")
        self.network["dcaCodeId"] = code_id
        write_artifact(self.network, "localterra")
        return code_id

    def instantiate_dca_contract(self, dca_code_id: int):
        instantiate_msg = {
            "factory_addr":
            "terra1qnmggqv3u03axw69cn578hukqhl4f2ze2k403ykcdlhj98978u7stv7fyj",
            "max_hops": 3,
            "max_spread": "0.5",
            "per_hop_fee": "100000",
            "router_addr": self.network["routerAddress"],
            "whitelisted_tokens": [
                TokenAsset(self.network["tokenAddresses"]
                           ["AAA"]).get_info().to_dict(),
                TokenAsset(self.network["tokenAddresses"]
                           ["BBB"]).get_info().to_dict(),
                TokenAsset(self.network["tokenAddresses"]
                           ["CCC"]).get_info().to_dict(),
                TokenAsset(self.network["tokenAddresses"]
                           ["DDD"]).get_info().to_dict(),
                NativeAsset("uluna").get_info().to_dict(),
            ],
            "whitelisted_fee_assets": [
                TokenAsset(self.network["tokenAddresses"]
                           ["CCC"], "1000").get_asset(),
                TokenAsset(self.network["tokenAddresses"]
                           ["AAA"], "2000").get_asset(),
                NativeAsset("uluna", "3000").get_asset(),
            ]
        }

        contract_address = DCA(self.terra, self.wallet).instantiate(
            dca_code_id, instantiate_msg)

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
        dca = DCA(self.terra, self.wallet, self.network["dcaAddress"])

        dca.execute_create_oder(
            TokenAsset(self.network["tokenAddresses"]["AAA"], "1000000"),
            NativeAsset("uluna").get_info(),
            10, 10000, None)

        dca.execute_create_oder(
            TokenAsset(self.network["tokenAddresses"]["AAA"], "1000000"),
            TokenAsset(self.network["tokenAddresses"]["CCC"]).get_info(),
            10, 10000, self.get_block_time_second()+10)

    def add_user_tip_balance(self):
        dca = DCA(self.terra, self.wallet, self.network["dcaAddress"])

        asset1 = TokenAsset(
            self.network["tokenAddresses"]["CCC"], "1000000")
        asset2 = NativeAsset("uluna", "1000000")
        dca.execute_add_bot_tip([asset1, asset2])


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    s = Setup()
    # s.deploy_dca_contract()
    # s.create_test_orders()
    # s.add_user_tip_balance()
