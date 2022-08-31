
from operator import ne
from typing import Any, Optional
from terra_sdk.client.localterra import LocalTerra
from terra_sdk.core import Coins
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from terra_sdk.core.bech32 import AccAddress
from terra_sdk.client.lcd import LCDClient, Wallet
from bot.util import TokenAsset, NativeAsset,\
    Asset, read_artifact, write_artifact
from bot.dca import DCA
from typing import List


def upload_dca_contract(terra: LCDClient,
                        wallet: Wallet) -> str:
    network = read_artifact("localterra")

    code_id = DCA(terra, wallet).upload_contract(
        "tests/artifacts/astroport_dca_module.wasm")
    network["dcaCodeId"] = code_id
    write_artifact(network, "localterra")
    return code_id


def instantiate_dca_contract(terra: LCDClient,
                             wallet: Wallet, dca_code_id: int):
    network = read_artifact("localterra")
    instantiate_msg = {
        "factory_addr":
        "terra1qnmggqv3u03axw69cn578hukqhl4f2ze2k403ykcdlhj98978u7stv7fyj",
        "max_hops": 3,
        "max_spread": "0.5",
        "per_hop_fee": "100000",
        "router_addr": network["routerAddress"],
        "whitelisted_tokens": [
            TokenAsset(network["tokenAddresses"]["AAA"]).get_info().to_dict(),
            TokenAsset(network["tokenAddresses"]["BBB"]).get_info().to_dict(),
            TokenAsset(network["tokenAddresses"]["CCC"]).get_info().to_dict(),
            TokenAsset(network["tokenAddresses"]["DDD"]).get_info().to_dict(),
            NativeAsset("uluna").get_info().to_dict(),
        ],
        "whitelisted_fee_assets": [
            TokenAsset(network["tokenAddresses"]["CCC"], "100000").get_asset(),
            TokenAsset(network["tokenAddresses"]["AAA"], "200000").get_asset(),
            NativeAsset("uluna", "300000").get_asset(),
        ]
    }

    contract_address = DCA(terra, wallet).instantiate(
        dca_code_id, instantiate_msg)

    network["dcaAddress"] = contract_address
    write_artifact(network, "localterra")
    print("dca contract_address=", contract_address)


def deploy_dca_contract():
    terra = LocalTerra()
    wallet = terra.wallets["test1"]

    code_id = upload_dca_contract(terra, wallet)
    instantiate_dca_contract(terra, wallet, int(code_id))


def get_block_time_second(terra: LCDClient) -> int:
    from dateutil.parser import parse
    time_string = terra.tendermint.block_info()['block']['header']['time']
    date_time = parse(time_string)
    return round(date_time.timestamp())


def create_test_orders():
    network = read_artifact("localterra")
    terra = LocalTerra()
    test_wallet_1 = terra.wallets["test1"]

    dca = DCA(terra, test_wallet_1, network["dcaAddress"])

    dca.execute_create_oder(
        TokenAsset(network["tokenAddresses"]["AAA"], "1000000"),
        NativeAsset("uluna").get_info(),
        10, 1000000, None)

    dca.execute_create_oder(
        TokenAsset(network["tokenAddresses"]["AAA"], "1000000"),
        TokenAsset(network["tokenAddresses"]["CCC"]).get_info(),
        10, 1000000, get_block_time_second(terra)+10)


def add_user_tip_balance():
    network = read_artifact("localterra")
    terra = LocalTerra()
    test_wallet_1 = terra.wallets["test1"]

    dca = DCA(terra, test_wallet_1, network["dcaAddress"])

    asset1 = TokenAsset(
        network["tokenAddresses"]["CCC"], "1000000")
    asset2 = NativeAsset("uluna", "1000000")
    dca.execute_add_bot_tip([asset1, asset2])
    # dca.execute_add_bot_tip(asset1)


if __name__ == "__main__":
    # deploy_dca_contract()
    # create_test_orders()
    add_user_tip_balance()
    pass
