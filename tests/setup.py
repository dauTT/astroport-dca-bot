
from typing import Any, Optional
from terra_sdk.client.localterra import LocalTerra
from terra_sdk.core import Coins
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from bot.util import AssetClass, AssetInfo, perform_transactions,\
    upload_contract, instantiate_contract, TokenAsset, NativeAsset,\
    Asset, read_artifact, write_artifact
from terra_sdk.core.bech32 import AccAddress
from terra_sdk.client.lcd import LCDClient, Wallet


def upload_dca_contract(terra: LCDClient,
                        wallet: Wallet) -> str:
    network_json = read_artifact("localterra")

    code_id = upload_contract(
        terra, wallet, "tests/artifacts/astroport_dca_module.wasm")
    network_json["dcaCodeId"] = code_id
    write_artifact(network_json, "localterra")
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
            TokenAsset(network["tokenAddresses"]["CCC"]).get_asset(),
            TokenAsset(network["tokenAddresses"]["AAA"]).get_asset(),
            NativeAsset("uluna").get_asset(),
        ]
    }

    contract_address = instantiate_contract(
        terra, wallet, dca_code_id, instantiate_msg, "dca contract", Coins([]))

    network["dcaAddress"] = contract_address
    write_artifact(network, "localterra")
    print("dca contract_address=", contract_address)


def deploy_dca_contract():
    terra = LocalTerra()
    wallet = terra.wallets["test1"]

    code_id = upload_dca_contract(terra, wallet)
    instantiate_dca_contract(terra, wallet, int(code_id))


def update_user_config(terra: LCDClient,
                       wallet: Wallet,
                       max_hops: Optional[int],
                       max_spread: Optional[float]):
    pass


def create_oder(terra: LCDClient,
                wallet: Wallet, initial_asset: Asset,
                target_asset: AssetInfo, interval: int,
                dca_amount: int, first_purchase: Optional[int]):
    network = read_artifact("localterra")

    funds = Coins([])
    msgs = []
    if initial_asset.is_native():
        funds = Coins([initial_asset.to_coin()])
    else:
        msg_increase_allowance = MsgExecuteContract(
            wallet.key.acc_address,
            AccAddress(initial_asset.get_info().to_dict()
                       ["token"]["contract_addr"]),
            {
                "increase_allowance": {
                    "spender": network["dcaAddress"],
                    "amount": initial_asset.get_asset()["amount"],
                }
            }
        )

        msgs.append(msg_increase_allowance)

    msg_create_dca_order = MsgExecuteContract(
        wallet.key.acc_address,
        AccAddress(network["dcaAddress"]),
        {
            "create_dca_order": {
                "initial_asset": initial_asset.get_asset(),
                "target_asset": target_asset.to_dict(),
                "interval": interval,
                "dca_amount": str(dca_amount),
                "first_purchase": first_purchase
            }},
        funds
    )

    msgs.append(msg_create_dca_order)
    perform_transactions(terra, wallet, msgs)


def get_block_time_second(terra: LCDClient) -> int:
    from dateutil.parser import parse
    time_string = terra.tendermint.block_info()['block']['header']['time']
    date_time = parse(time_string)
    return round(date_time.timestamp())


def create_test_orders():
    network = read_artifact("localterra")
    terra = LocalTerra()
    test_wallet_1 = terra.wallets["test1"]

    create_oder(terra, test_wallet_1,
                TokenAsset(network["tokenAddresses"]["AAA"], "1000000"),
                NativeAsset("uluna").get_info(),
                10, 1000000, None)

    create_oder(terra, test_wallet_1,
                TokenAsset(network["tokenAddresses"]["AAA"], "1000000"),
                TokenAsset(network["tokenAddresses"]["CCC"]).get_info(),
                10, 1000000, get_block_time_second(terra)+10)


if __name__ == "__main__":
    # deploy_dca_contract()
    # create_test_orders()
    pass
