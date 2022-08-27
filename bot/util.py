from terra_sdk.core import Coin, Coins
import json
import os
import base64
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.msg import Msg
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract
from terra_sdk.core.wasm.data import AccessConfig
from terra_sdk.core.tx import Tx
from terra_sdk.core.bech32 import AccAddress
from terra_sdk.core.broadcast import BlockTxBroadcastResult
# from terra_sdk.core.fee import Fee
from terra_proto.cosmwasm.wasm.v1 import AccessType
from terra_sdk.client.lcd import LCDClient, Wallet
from typing import Dict, List, Any, Optional
# import traceback
from abc import ABC, abstractmethod
from enum import Enum


ARTIFACTS_PATH = "localterra"


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


def upload_contract(
    terra: LCDClient,
    wallet: Wallet,
    filepath: str
) -> str:
    contract_file = open(filepath, "rb")
    file_bytes = base64.b64encode(contract_file.read()).decode()
    store_code = MsgStoreCode(wallet.key.acc_address, file_bytes, AccessConfig(
        AccessType.ACCESS_TYPE_EVERYBODY,   AccAddress("")))
    store_code_tx = wallet.create_and_sign_tx(CreateTxOptions(
        msgs=[store_code]))
    store_code_tx_result = terra.tx.broadcast(store_code_tx)
    print(store_code_tx_result.logs)
    if store_code_tx_result.logs == None:
        return ""
    return store_code_tx_result.logs[0].events_by_type["store_code"]["code_id"][0]


def instantiate_contract(
    terra: LCDClient,
    wallet: Wallet,
    codeId: int,
    msg: Any,
    label: str,
    funds: Coins,
    admin_address: AccAddress = AccAddress(""),
) -> str:
    instantiate_msg = MsgInstantiateContract(
        wallet.key.acc_address,
        admin_address,
        codeId,
        label,
        msg,
        funds

    )

    instantiate_tx_result = performTransaction(terra,
                                               wallet,
                                               instantiate_msg)

    print("instantiate_tx_result: ", instantiate_tx_result)

    if instantiate_tx_result.logs == None:
        return ""
    contract_address = instantiate_tx_result.logs[0].events_by_type[
        "instantiate"
    ]["_contract_address"][0]

    return contract_address


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


def performTransaction(
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


def get_user_dca_orders(terra: LCDClient, dca_address: str, user_address: str) -> Any:
    return terra.wasm.contract_query(dca_address, {
        "user_dca_orders": {
            "user": user_address
        }
    })


def get_user_config(terra: LCDClient, dca_address: str, user_address: str) -> Any:
    return terra.wasm.contract_query(dca_address, {
        "user_config": {
            "user": user_address
        }
    })
