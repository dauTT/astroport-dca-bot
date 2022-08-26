from terra_sdk.core import Coin, Coins
import json
import os
import base64
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.msg import Msg
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract
from terra_sdk.core.wasm.data import AccessConfig
from terra_sdk.core.tx import Tx
from terra_sdk.core.broadcast import BlockTxBroadcastResult
# from terra_sdk.core.fee import Fee
from terra_proto.cosmwasm.wasm.v1 import AccessType  # AccessConfig

from terra_sdk.client.lcd import LCDClient, Wallet
from typing import List, Any
import traceback


ARTIFACTS_PATH = "tests/localterra"


def write_artifact(data, name):

    file_path = os.path.join(ARTIFACTS_PATH, name + ".json")
    with open(file_path, "w") as outfile:
        # Writing data to a file
        json.dump(data, outfile, indent=4)


def read_artifact(name):
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
        AccessType.ACCESS_TYPE_EVERYBODY, ""))
    store_code_tx = wallet.create_and_sign_tx(CreateTxOptions(
        msgs=[store_code]))
    store_code_tx_result = terra.tx.broadcast(store_code_tx)
    print(store_code_tx_result.logs)

    return store_code_tx_result.logs[0].eventsByType.store_code.code_id[0]


def instantiate_contract(
    terra: LCDClient,
    wallet: Wallet,
    codeId: int,
    msg: object,
    label: str,
    funds: Coins,
    admin_address: str = None,
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
    contract_address = instantiate_tx_result.logs[0].events_by_type[
        "instantiate"
    ]["_contract_address"][0]

    return contract_address


def perform_transactions(
    terra: LCDClient,
    wallet: Wallet,
    msgs: List[Msg]
) -> BlockTxBroadcastResult:
    try:
        signed_txs = create_transactions(wallet, msgs)
        result = broadcast_transaction(terra, signed_txs)
        return result
    except:
        traceback.print_exc()


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
    try:
        signed_tx = create_transaction(wallet, msg)
        result = broadcast_transaction(terra, signed_tx)
        return result
    except:
        traceback.print_exc()


class NativeAsset:

    def __init__(self, denom, amount="0"):
        self.denom = denom
        self.amount = amount

    def getInfo(self):
        return {
            "native_token": {
                "denom": self.denom,
            }
        }

    def getAsset(self):
        return {
            "info": self.getInfo(),
            "amount": self.amount,
        }

    def getDenom(self):
        return self.denom

    def toCoin(self):
        return Coin(self.denom, self.amount)


class TokenAsset:

    def __init__(self, addr, amount="0"):
        self.addr = addr
        self.amount = amount

    def getInfo(self):
        return {
            "token": {
                "contract_addr": self.addr,
            },
        }

    def getAsset(self):
        return {
            "info": self.getInfo(),
            "amount": self.amount,
        }

    def toCoin(self):
        return None

    def getDenom(self):
        return self.addr
