import json
import os
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.msg import Msg
from terra_sdk.core.tx import Tx
from terra_sdk.core.broadcast import BlockTxBroadcastResult
from terra_sdk.client.lcd import LCDClient, Wallet
from typing import List, Any
import logging
from bot.db.table.whitelisted_hop import WhitelistedHop
from bot.db.table.whitelisted_token import WhitelistedToken
from bot.type import AssetClass, Asset, AssetInfo, Order, \
    NativeAsset, TokenAsset, AstroSwap

logger = logging.getLogger(__name__)


ARTIFACTS_PATH = "tests/localterra"


def write_artifact(data: Any, name: str):
    file_path = os.path.join(ARTIFACTS_PATH, name + ".json")
    with open(file_path, "w") as outfile:
        # Writing data to a file
        json.dump(data, outfile, indent=4)


def read_artifact(name: str):
    file_path = os.path.join(ARTIFACTS_PATH, name + ".json")
    with open(file_path, 'r') as openfile:
        network_json = json.load(openfile)
    return network_json


def perform_transactions(
    terra: LCDClient,
    wallet: Wallet,
    msgs: List[Msg]
) -> BlockTxBroadcastResult:
    signed_txs = create_transactions(wallet, msgs)
    output = broadcast_transaction(terra, signed_txs)
    logger.debug("""perform_transactions output: """, output)
    return output


def create_transaction(wallet: Wallet, msg: Msg) -> Tx:
    return wallet.create_and_sign_tx(
        CreateTxOptions(msgs=[msg]))


def create_transactions(wallet: Wallet, msgs: List[Msg]) -> Tx:
    return wallet.create_and_sign_tx(
        CreateTxOptions(msgs))


def broadcast_transaction(terra: LCDClient, signed_tx: Tx) -> BlockTxBroadcastResult:
    return terra.tx.broadcast(signed_tx)


def perform_transaction(
    terra: LCDClient,
    wallet: Wallet,
    msg: Msg
) -> BlockTxBroadcastResult:
    signed_tx = create_transaction(wallet, msg)
    output = broadcast_transaction(terra, signed_tx)
    logger.debug("""perform_transactions output: """, output)
    return output


def parse_dict_to_asset(d: dict) -> Asset:
    assert "info" in d, "Expected info key in the dictionary"
    err_msg = "Expected key={} or key={} to be in in dictionary".format(
        AssetClass.TOKEN.value, AssetClass.NATIVE_TOKEN.value)
    assert AssetClass.TOKEN.value in d["info"] or AssetClass.NATIVE_TOKEN.value in d["info"], err_msg

    if AssetClass.TOKEN.value in d["info"]:
        return TokenAsset(d["info"]["token"]["contract_addr"], d["amount"])
    else:
        return NativeAsset(d["info"]["native_token"]["denom"], d["amount"])


def parse_dict_to_asset_info(d: dict) -> AssetInfo:
    err_msg = "Expected key={} or key={} to be in in dictionary".format(
        AssetClass.TOKEN.value, AssetClass.NATIVE_TOKEN.value)
    assert AssetClass.TOKEN.value in d or AssetClass.NATIVE_TOKEN.value in d, err_msg

    if AssetClass.TOKEN.value in d:
        assert "contract_addr" in d[AssetClass.TOKEN.value], err_msg
        return AssetInfo(AssetClass.TOKEN, d[AssetClass.TOKEN.value]["contract_addr"])
    else:
        assert "denom" in d[AssetClass.NATIVE_TOKEN.value], err_msg
        return AssetInfo(AssetClass.NATIVE_TOKEN, d[AssetClass.NATIVE_TOKEN.value]["denom"])


def parse_dict_to_order(d: dict) -> Order:
    order = d["order"]
    for key in ['id', 'initial_asset', 'target_asset', 'interval', 'last_purchase', 'dca_amount']:
        assert key in order, "Expected key={} in the order dict={}".format(
            key, order)
    return Order(id=order['id'],
                 token_allowance=int(d.get("token_allowance", "0")),
                 initial_asset=parse_dict_to_asset(
                     order["initial_asset"]),
                 target_asset=parse_dict_to_asset_info(
                     order["target_asset"]),
                 interval=order["interval"],
                 last_purchase=order["last_purchase"],
                 dca_amount=int(order["dca_amount"]))


def parse_hops_from_string(hops: str,  whithelisted_tokens: List[WhitelistedToken],
                           whithelisted_hops: List[WhitelistedHop]) -> List[AstroSwap]:

    logger.debug("parse_hops_from_string: hops: {}".format(hops))

    output: List[AstroSwap] = []

    map_wt = {}
    for wt in whithelisted_tokens:
        ac = AssetClass.NATIVE_TOKEN if wt.asset_class == AssetClass.NATIVE_TOKEN.value else AssetClass.TOKEN
        map_wt[wt.denom] = AssetInfo(ac, str(wt.denom))
    map_hops = {}
    for h in whithelisted_hops:
        map_hops[h.id] = h

    logger.debug("map_hops={}".format(map_hops))
    l = hops.split("><")
    length = len(l)
    if length == 0:
        assert length > 0

    for h in l:
        hop = h.replace("<", "").replace(">", "")
        hop_id = int(hop)
        if hop.__contains__("inverse-"):
            hop_id = int(hop.replace("inverse-", ""))

        assert hop_id in map_hops, "Missing hop_id={} in the whitelisted_hop={}".format(
            hop_id, whithelisted_hops)

        offer_denom: str = map_hops[hop_id].offer_denom
        ask_denom: str = map_hops[hop_id].ask_denom
        assert offer_denom in map_wt, "Missing offer_denom={} in the whithelisted_tokens={}".format(offer_denom,
                                                                                                    whithelisted_tokens)
        assert ask_denom in map_wt, "Missing ask_denom={} in the whithelisted_tokens={}".format(ask_denom,
                                                                                                whithelisted_tokens)
        offer_asset_info = map_wt[offer_denom]
        ask_asset_info = map_wt[ask_denom]

        if hop.__contains__("inverse-"):
            output.append(AstroSwap(ask_asset_info, offer_asset_info))
        else:
            output.append(AstroSwap(offer_asset_info, ask_asset_info))

    logger.debug("SwapOperations: {}".format(output))
    return output


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.INFO)
    # from bot.db.database import Database

    # hops_string = "<2><3>"

    # db = Database()
    # db.get_whitelisted_tokens()

    # wl_hops = db.get_whitelisted_hops()
    # # print(wl_hops)
    # parse_hops_from_string(
    #     hops_string, db.get_whitelisted_tokens(), wl_hops)

    pass
