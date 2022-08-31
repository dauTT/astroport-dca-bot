from terra_sdk.core import Coin, Coins
import json
import os
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.msg import Msg
from terra_sdk.core.tx import Tx
from terra_sdk.core.broadcast import BlockTxBroadcastResult
from terra_sdk.client.lcd import LCDClient, Wallet
from typing import Dict, List, Any, TypedDict
from abc import ABC, abstractmethod
from enum import Enum


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
    print("perform_transactions output:", output)
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
    print("perform_transaction output:", output)
    return output


class AssetClass(Enum):
    NATIVE_TOKEN = "native_token"
    TOKEN = "token"


class AssetInfo():

    def __init__(self, asset_class: AssetClass, denom: str):
        self.asset_class = asset_class
        self.denom = denom

    def to_dict(self) -> Any:
        key = "denom" if self.asset_class == AssetClass.NATIVE_TOKEN else "contract_addr"
        return {
            self.asset_class.value: {
                key: self.denom
            }
        }


class AstroSwap:

    def __init__(self, offer_asset_info: AssetInfo,
                 ask_asset_info: AssetInfo):
        self.offer_asset_info = offer_asset_info
        self.ask_asset_info = ask_asset_info

    def to_dict(self):
        return {
            "astro_swap": {
                'offer_asset_info':  self.offer_asset_info.to_dict(),
                'ask_asset_info': self.ask_asset_info.to_dict()
            }
        }

    def __repr__(self):
        return "{}".format(self.to_dict())


class Asset(ABC):

    @abstractmethod
    def get_info(self) -> AssetInfo:
        pass

    @abstractmethod
    def get_asset(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_denom(self) -> str:
        pass

    @abstractmethod
    def to_coin(self) -> Coin:
        pass

    @abstractmethod
    def is_native(self) -> bool:
        pass


class Order(TypedDict):
    id: int
    token_allowance: str
    initial_asset: Asset
    target_asset: AssetInfo
    interval: int
    last_purchase: int
    dca_amount: str


class TokenAsset(Asset):

    def __init__(self, addr: str, amount: str = "0"):
        self.addr = addr
        self.amount = amount

    def get_info(self) -> AssetInfo:
        return AssetInfo(AssetClass.TOKEN, self.addr)

    def get_asset(self) -> Dict[str, Any]:
        return {
            "info": self.get_info().to_dict(),
            "amount": self.amount,
        }

    def to_coin(self) -> Coin:
        return Coin("", 0)

    def get_denom(self) -> str:
        return self.addr

    def is_native(self) -> bool:
        return False


class NativeAsset(Asset):

    def __init__(self, denom: str, amount: str = "0"):
        self.denom = denom
        self.amount = amount

    def get_info(self) -> AssetInfo:
        return AssetInfo(AssetClass.NATIVE_TOKEN, self.denom)

    def get_asset(self) -> Dict[str, Any]:
        return {
            "info": self.get_info().to_dict(),
            "amount": self.amount,
        }

    def get_denom(self) -> str:
        return self.denom

    def to_coin(self) -> Coin:
        return Coin(self.denom, int(self.amount))

    def is_native(self) -> bool:
        return True


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
                 token_allowance=d.get("token_allowance", ""),
                 initial_asset=parse_dict_to_asset(
                     order["initial_asset"]),
                 target_asset=parse_dict_to_asset_info(
                     order["target_asset"]),
                 interval=order["interval"],
                 last_purchase=order["last_purchase"],
                 dca_amount=order["dca_amount"])


def parse_hops_from_string(hops: str,  whithelisted_tokens: List[dict],
                           whithelisted_hops: List[dict]) -> List[AstroSwap]:
    output: List[AstroSwap] = []

    map_wt = {}
    for wt in whithelisted_tokens:
        ac = AssetClass.NATIVE_TOKEN if wt["asset_class"] == AssetClass.NATIVE_TOKEN.value else AssetClass.TOKEN
        map_wt[wt["denom"]] = AssetInfo(ac, wt["denom"])
    map_hops = {}
    for h in whithelisted_hops:
        map_hops[h["id"]] = h

    l = hops.split("><")
    length = len(l)
    if length == 0:
        assert length > 0

    for hop in l:
        hop = l[0].replace("<", "").replace(">", "")
        hop_id = int(hop)
        if hop.__contains__("inverse-"):
            hop_id = int(hop.replace("inverse-", ""))

        assert hop_id in map_hops, "Missing hop_id={} in the whitelisted_hop={}".format(
            hop_id, whithelisted_hops)

        offer_denom = map_hops[hop_id]['offer_denom']
        ask_denom = map_hops[hop_id]['ask_denom']
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
    return output


if __name__ == "__main__":
    pass
    # w = [
    #     TokenAsset(network["tokenAddresses"]["CCC"], "100000"),
    #     TokenAsset(network["tokenAddresses"]["AAA"], "200000"),
    #     NativeAsset("uluna", "300000"),
    # ]

    # dca.execute_update_config(whitelisted_fee_assets=w)
