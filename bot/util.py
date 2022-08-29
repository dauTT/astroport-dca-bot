from terra_sdk.core import Coin, Coins
import json
import os
import base64
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.msg import Msg
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from terra_sdk.core.wasm.data import AccessConfig
from terra_sdk.core.tx import Tx
from terra_sdk.core.bech32 import AccAddress
from terra_sdk.core.broadcast import BlockTxBroadcastResult
from terra_sdk.client.localterra import LocalTerra
# from terra_sdk.core.fee import Fee
from terra_proto.cosmwasm.wasm.v1 import AccessType
from terra_sdk.client.lcd import LCDClient, Wallet
from typing import Dict, List, Any, Optional, TypedDict
# import traceback
from abc import ABC, abstractmethod
from enum import Enum
import logging
from logging.handlers import RotatingFileHandler


BASE_DIR = "../logs"


def init_log():

    file_name = os.path.join(BASE_DIR, 'log', 'bot.log')
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename=file_name, format=format, level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(format)
    file_handler = RotatingFileHandler(file_name,
                                       maxBytes=1024 * 1024 * 50,
                                       backupCount=10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


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

    def get_denom(self):
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

    def get_denom(self):
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
        return TokenAsset(d["info"]["token"], d["amount"])
    else:
        return NativeAsset(d["info"]["native_token"], d["amount"])


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
    for key in ['id', 'initial_asset', 'target_asset', 'interval', 'last_purchase', 'dca_amount']:
        assert key in d, "Expected key={} in the dictionary".format(key)
    return Order(id=d['id'],
                 token_allowance=d.get("token_allowance", ""),
                 initial_asset=parse_dict_to_asset(d["initial_asset"]),
                 target_asset=parse_dict_to_asset_info(d["target_asset"]),
                 interval=d["interval"],
                 last_purchase=d["last_purchase"],
                 dca_amount=d["dca_amount"])


class DCA:

    def __init__(self, terra: LCDClient, wallet: Wallet, dca_address: str = ""):
        self.terra = terra
        self.wallet = wallet
        self.dca_address = dca_address

    def set_dca_address(self, dca_address: str):
        self.dca_address = dca_address

    def get_whitelisted_astro_swaps(self):
        self.query_get_config()

    def get_astro_pools(self, fatctory_address):
        return self.terra.wasm.contract_query(fatctory_address, {
            "pairs": {}
        })

    def query_get_user_dca_orders(self, user_address: str) -> dict:
        assert self.dca_address != "", "No dca contract address given"

        return self.terra.wasm.contract_query(self.dca_address, {
            "user_dca_orders": {
                "user": user_address
            }
        })

    def query_get_user_config(self, user_address: str) -> dict:
        assert self.dca_address != "", "No dca contract address given"

        return self.terra.wasm.contract_query(self.dca_address, {
            "user_config": {
                "user": user_address
            }
        })

    def query_get_config(self) -> dict:
        assert self.dca_address != "", "No dca contract address given"

        return self.terra.wasm.contract_query(self.dca_address, {"config": {}})

    def instantiate(self, dca_code_id: int, msg: Any) -> str:
        instantiate_msg = MsgInstantiateContract(
            self.wallet.key.acc_address,
            AccAddress(""),
            dca_code_id,
            "dca contract",
            msg,
            Coins([])

        )

        instantiate_tx_result = perform_transaction(self.terra,
                                                    self.wallet,
                                                    instantiate_msg)

        print("instantiate_tx_result: ", instantiate_tx_result)

        if instantiate_tx_result.logs == None:
            return ""
        contract_address = instantiate_tx_result.logs[0].events_by_type[
            "instantiate"
        ]["_contract_address"][0]

        return contract_address

    def execute_create_oder(self, initial_asset: Asset,
                            target_asset: AssetInfo, interval: int,
                            dca_amount: int, first_purchase: Optional[int]):
        assert self.dca_address != "", "No dca contract address given"

        funds = Coins([])
        msgs = []
        if initial_asset.is_native():
            funds = Coins([initial_asset.to_coin()])
        else:
            msg_increase_allowance = MsgExecuteContract(
                self.wallet.key.acc_address,
                AccAddress(initial_asset.get_info().to_dict()
                           ["token"]["contract_addr"]),
                {
                    "increase_allowance": {
                        "spender": self.dca_address,
                        "amount": initial_asset.get_asset()["amount"],
                    }
                }
            )

            msgs.append(msg_increase_allowance)

        msg_create_dca_order = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_address),
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
        perform_transactions(self.terra, self.wallet, msgs)

    def execute_update_user_config(self,
                                   max_hops: Optional[int],
                                   max_spread: Optional[str]):

        msg = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_address),
            {
                "update_user_config": {
                    "max_hops": max_hops,
                    "max_spread": max_spread,

                }},
            Coins([])
        )

        perform_transaction(self.terra, self.wallet, msg)

    def execute_update_config(self, max_hops: Optional[int] = None,
                              max_spread: Optional[str] = None,
                              whitelisted_tokens: Optional[List[Asset]] = None,
                              whitelisted_fee_assets: Optional[List[Asset]] = None):
        w_tokens = None if whitelisted_tokens == None else [
            a.get_asset() for a in whitelisted_tokens]

        w_fee_assets = None if whitelisted_fee_assets == None else [
            a.get_asset() for a in whitelisted_fee_assets]

        msg = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_address),
            {
                "update_config": {
                    "max_hops": max_hops,
                    "max_spread": max_spread,
                    "whitelisted_tokens": w_tokens,
                    "whitelisted_fee_assets": w_fee_assets
                }},
            Coins([])
        )

        perform_transaction(self.terra, self.wallet, msg)

    def execute_perform_dca_purchase(self, user_address: str, id: int, hops: List[AstroSwap],
                                     fee_redeem: List[Asset]):

        msg = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_address), {
                "perform_dca_purchase": {
                    "user": user_address,
                    "id": id,
                    "hops": [h.to_dict() for h in hops],
                    "fee_redeem": [a.get_asset() for a in fee_redeem]

                }},
            Coins([])
        )

        perform_transaction(self.terra, self.wallet, msg)

    def execute_add_bot_tip(self, assets: List[Asset]):
        funds = []
        msgs = []
        for asset in assets:
            if asset.is_native():
                funds.append(asset.to_coin())
            else:
                # increase allowance msg
                msgs.append(MsgExecuteContract(
                    self.wallet.key.acc_address,
                    AccAddress(asset.get_info().to_dict()
                               ["token"]["contract_addr"]),
                    {
                        "increase_allowance": {
                            "spender": self.dca_address,
                            "amount": asset.get_asset()["amount"],
                        }
                    }
                )
                )

        msgs.append(MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_address), {
                "add_bot_tip": {"assets": [a.get_asset() for a in assets]}
            },
            Coins(funds)
        ))

        perform_transactions(self.terra, self.wallet, msgs)

    def upload_contract(self,
                        filepath: str
                        ) -> str:
        contract_file = open(filepath, "rb")
        file_bytes = base64.b64encode(contract_file.read()).decode()
        store_code = MsgStoreCode(self.wallet.key.acc_address, file_bytes, AccessConfig(
            AccessType.ACCESS_TYPE_EVERYBODY,   AccAddress("")))
        store_code_tx = self.wallet.create_and_sign_tx(CreateTxOptions(
            msgs=[store_code]))
        store_code_tx_result = self.terra.tx.broadcast(store_code_tx)
        print(store_code_tx_result.logs)
        if store_code_tx_result.logs == None:
            return ""
        return store_code_tx_result.logs[0].events_by_type["store_code"]["code_id"][0]


if __name__ == "__main__":

    network = read_artifact("localterra")
    terra = LocalTerra()
    test_wallet_1 = terra.wallets["test1"]
    print(test_wallet_1.key.acc_address)
    contract = network["factoryAddress"]
    result = terra.wasm.contract_query(contract, {"config": {}})
    print(result)

    dca_contract = network["dcaAddress"]
    dca = DCA(terra, test_wallet_1, dca_contract)

    # w = [
    #     TokenAsset(network["tokenAddresses"]["CCC"], "100000"),
    #     TokenAsset(network["tokenAddresses"]["AAA"], "200000"),
    #     NativeAsset("uluna", "300000"),
    # ]

    # dca.execute_update_config(whitelisted_fee_assets=w)

    pass
