
from terra_sdk.client.localterra import LocalTerra
# from terra_sdk.core.fee import Fee
from terra_sdk.client.lcd import LCDClient, Wallet
from bot.util import read_artifact
from bot.type import TokenAsset, NativeAsset,\
    AstroSwap, SimulateSwapOperation

import logging

logger = logging.getLogger(__name__)


class Router:

    def __init__(self, terra: LCDClient, wallet: Wallet, router_address: str, factory_address):
        self.terra = terra
        self.wallet = wallet
        self.router_address = router_address
        self.factory_address = factory_address

    def get_astro_pools(self, fatctory_address):
        return self.terra.wasm.contract_query(fatctory_address, {
            "pairs": {}
        })

    def simulate_swap_operations(self, swo: SimulateSwapOperation):
        return self.terra.wasm.contract_query(self.router_address,
                                              swo.to_dict())


if __name__ == "__main__":
    network = read_artifact("localterra")
    terra = LocalTerra()
    wallet = terra.wallets["test1"]

    AAA = TokenAsset(network["tokenAddresses"]["AAA"])
    BBB = TokenAsset(network["tokenAddresses"]["BBB"])
    LUNA = NativeAsset("uluna")

    operations = [AstroSwap(AAA.get_info(), BBB.get_info()),
                  AstroSwap(BBB.get_info(), LUNA.get_info())]
    sso = SimulateSwapOperation("100000", operations)

    print(sso)

    r = Router(terra, wallet,
               network["routerAddress"], network["factoryAddress"])
    res = r.simulate_swap_operations(sso)
    print(res)

    pass
