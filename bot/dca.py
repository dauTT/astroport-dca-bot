
from terra_sdk.core import Coins
import base64
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract,\
    MsgExecuteContract
from terra_sdk.core.wasm.data import AccessConfig
from terra_sdk.core.bech32 import AccAddress
from terra_proto.cosmwasm.wasm.v1 import AccessType
from terra_sdk.client.lcd import LCDClient, Wallet
from typing import List, Any, Optional
from bot.util import perform_transaction, Asset, AssetInfo, \
    perform_transactions, AstroSwap
from bot.type import AstroSwap, SimulateSwapOperation

import json

import logging

logger = logging.getLogger(__name__)


class DCA:

    def __init__(self, terra: LCDClient, wallet: Wallet,  dca_addr: str = ""):
        self.terra = terra
        self.wallet = wallet
        self.dca_addr = dca_addr
        self.factory_addr = None
        self.router_addr = None

    def set_dca_addr(self, dca_addr: str):
        self.dca_addr = dca_addr

    def check_dca_addr(self):
        assert self.dca_addr != "", "No dca contract address given"

    def get_factory_addr(self) -> str:
        """ It is safe to cache the factory address because once the dca contract is deployed this address can't be modified.
        """
        if self.factory_addr == None:
            self.factory_addr = self.query_get_config()["factory_addr"]
        return self.factory_addr

    def get_router_addr(self) -> str:
        """ It is safe to cache the router address because once the dca contract is deployed this address can't be modified.
        """
        if self.router_addr == None:
            self.router_addr = self.query_get_config()["router_addr"]
        return self.router_addr

    def _log_debug_output(self, output: dict):
        logger.debug(""" result :
        {} """.format(json.dumps(output, indent=2)))

    def get_astro_pools(self):
        output = self.terra.wasm.contract_query(self.get_factory_addr(), {
            "pairs": {}
        })
        self._log_debug_output(output)
        return output

    def simulate_swap_operations(self, swo: SimulateSwapOperation) -> int:
        output = self.terra.wasm.contract_query(self.get_router_addr(),
                                                swo.to_dict())

        return output["amount"]

    def query_get_user_dca_orders(self, user_address: str) -> List[dict]:
        logger.debug("query_get_user_dca_orders")
        self.check_dca_addr()

        output = self.terra.wasm.contract_query(self.dca_addr, {
            "user_dca_orders": {
                "user": user_address
            }
        })

        self._log_debug_output(output)
        return output

    def query_get_user_config(self, user_address: str) -> dict:
        logger.debug("query_get_user_config")
        self.check_dca_addr()

        output = self.terra.wasm.contract_query(self.dca_addr, {
            "user_config": {
                "user": user_address
            }
        })
        self._log_debug_output(output)
        return output

    def query_get_config(self) -> dict:
        logger.debug("query_get_config")
        self.check_dca_addr()

        output = self.terra.wasm.contract_query(
            self.dca_addr, {"config": {}})

        self._log_debug_output(output)
        return output

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

        self.check_dca_addr()

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
                        "spender": self.dca_addr,
                        "amount": initial_asset.get_asset()["amount"],
                    }
                }
            )

            msgs.append(msg_increase_allowance)

        msg_create_dca_order = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_addr),
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
        self.check_dca_addr()

        msg = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_addr),
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
        self.check_dca_addr()

        w_tokens = None if whitelisted_tokens == None else [
            a.get_asset() for a in whitelisted_tokens]

        w_fee_assets = None if whitelisted_fee_assets == None else [
            a.get_asset() for a in whitelisted_fee_assets]

        msg = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_addr),
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

        self.check_dca_addr()
        logger.info("***** call dca.execute_perform_dca_purchase: *****")
        logger.debug("hops:{}, fee_reedem={}".format(hops, fee_redeem))

        msg = MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_addr), {
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
        self.check_dca_addr()

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
                            "spender": self.dca_addr,
                            "amount": asset.get_asset()["amount"],
                        }
                    }
                )
                )

        msgs.append(MsgExecuteContract(
            self.wallet.key.acc_address,
            AccAddress(self.dca_addr), {
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
    # from terra_sdk.client.localterra import LocalTerra
    # from bot.util import read_artifact
    # network = read_artifact("localterra")
    # terra = LocalTerra()
    # test_wallet_1 = terra.wallets["test1"]
    # dca = DCA(terra, test_wallet_1, network["dcaAddress"])
    pass
