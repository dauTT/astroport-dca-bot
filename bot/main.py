from tokenize import Token
from util import DCA, AstroSwap, NativeAsset, Order, TokenAsset,\
    read_artifact, parse_dict_to_order, Asset
from terra_sdk.client.localterra import LocalTerra
from typing import TypedDict, List


def build_fee_redeem(hops_len: int,  user_tip_balance: List[Asset], whitelisted_fee_assets: List[Asset]) -> List[Asset]:
    """ The bot will try to take fee from the first asset in user_tip_balance. 
        If this this is not sufficient it will will consider also the second asset and so on.
        For each hop the bot can take a fee amount as configured in whitelisted_fee_assets.
        If user_tip_balance is not sufficient to pay the fees for the bot, this method will throw an error.
    """
    fee_redeem: List[Asset] = []
    hop_fee_map = {}
    for asset in whitelisted_fee_assets:
        hop_fee_map[asset.get_denom()] = int(asset.get_asset()["amount"])

    assert len(user_tip_balance) > 0, "user_tip_balance is empty!"

    h = hops_len
    for tip in user_tip_balance:
        amount = int(tip.get_asset()["amount"])
        tip_fee = hop_fee_map[tip.get_denom()]
        q = amount // tip_fee
        if q >= h:
            if tip.is_native():
                fee = tip_fee * h
                fee_redeem.append(NativeAsset(tip.get_denom(), str(fee)))
                h = 0
                break
        else:
            fee = tip_fee * q
            fee_redeem.append(NativeAsset(tip.get_denom(), str(fee)))
            h = h - q
    err_msg = """tip_balance={} is not sufficient to pays for fees 
                 based on hops_len={} and fees structure = {}""".format(user_tip_balance,
                                                                        hops_len, hop_fee_map)
    assert h == 0, err_msg

    return fee_redeem


def build_hops(order) -> List[AstroSwap]:
    hops: List[AstroSwap] = []

    return hops


def execute_purchase(user_address: str, id: int):

    terra = LocalTerra()
    bot_wallet = terra.wallets["test10"]
    network = read_artifact("localterra")

    dca = DCA(terra, bot_wallet, network["dcaAddress"])

    cfg_dca = dca.query_get_config()
    cfg_user = dca.query_get_user_config(user_address)

    max_hops = cfg_dca['max_hops'] if cfg_user['max_hops'] is None else cfg_user['max_hops']
    max_spread = cfg_dca['max_spread'] if cfg_user['max_spread'] is None else cfg_user['max_spread']
    tip_balance = cfg_user['tip_balance']

    print("tip_balance: ", tip_balance)
    whitelisted_fee_assets = cfg_dca['whitelisted_fee_assets']
    print("whitelisted_fee_assets: ", whitelisted_fee_assets)

    whitelisted_tokens = cfg_dca['whitelisted_tokens']

    user_orders = dca.query_get_user_dca_orders(user_address)
    order = None
    for o in user_orders:
        if o["order"]["id"] == id:
            order = parse_dict_to_order(o["order"])

    # check inteval?
    # hops = build_hops(order)
    # fee_redeem = build_fee_redeem(
    #     len(hops),  tip_balance, whitelisted_fee_assets)

    # print(order)

    # id = 1000
    # hops = [AstroSwap("a", "b"), AstroSwap("b", "d")]
    # fee_redeem = [TokenAsset("contract1", "100"),
    #               NativeAsset("denom1", "1000")]

    # dca.execute_perform_dca_purchase(user_address, id, hops, fee_redeem)


if __name__ == "__main__":
    user_address = "terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v"
    id = 1  # --> native target asset
    # id = 3  # --> token target asset
    execute_purchase(user_address, id)
