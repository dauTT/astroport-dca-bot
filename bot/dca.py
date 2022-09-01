
from terra_sdk.core import Coins
import base64
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from terra_sdk.core.wasm.data import AccessConfig
from terra_sdk.core.bech32 import AccAddress
from terra_sdk.client.localterra import LocalTerra
# from terra_sdk.core.fee import Fee
from terra_proto.cosmwasm.wasm.v1 import AccessType
from terra_sdk.client.lcd import LCDClient, Wallet
from typing import List, Any, Optional
from bot.util import perform_transaction, Asset, AssetInfo, \
    perform_transactions, AstroSwap, read_artifact
import json

import logging

logger = logging.getLogger(__name__)


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

    def query_get_user_dca_orders(self, user_address: str) -> List[dict]:
        assert self.dca_address != "", "No dca contract address given"

        output = self.terra.wasm.contract_query(self.dca_address, {
            "user_dca_orders": {
                "user": user_address
            }
        })

        logger.info("""query_get_user_dca_orders({}):
        {} """.format(user_address, json.dumps(output, indent=4)))
        return output

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
