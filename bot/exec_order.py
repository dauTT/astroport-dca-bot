from bot.db.table.dca_order import DcaOrder
from bot.type import AssetClass
from util import AstroSwap, NativeAsset,\
    read_artifact, Asset, parse_hops_from_string
from terra_sdk.client.localterra import LocalTerra
from typing import List
from bot.db.database import Database
from bot.dca import DCA
from bot.db_sync import Sync
import logging

logger = logging.getLogger(__name__)


class ExecOrder:

    def __init__(self):
        self.network = read_artifact("localterra")
        self.terra = LocalTerra()
        self.dca = DCA(
            self.terra, self.terra.wallets["test1"], self.network["dcaAddress"])
        self.db = Database()

    def build_fee_redeem(self, user_address: str,  hops_len: int) -> List[Asset]:
        """ The bot will try to take fee from the first asset in user_tip_balance.
            If this this is not sufficient it will will consider also the second asset and so on.
            For each hop the bot can take a fee amount as configured in whitelisted_fee_assets.
            If user_tip_balance is not sufficient to pay the fees for the bot, this method will throw an error.
        """

        user_tip_balances = self.db.get_user_tip_balance(user_address)
        whitelisted_fee_assets = self.db.get_whitelisted_fee_asset()

        fee_redeem: List[Asset] = []
        hop_fee_map = {}
        for asset in whitelisted_fee_assets:
            hop_fee_map[asset.denom] = int(str(asset.amount))
        assert len(user_tip_balances) > 0, "user_tip_balance is empty!"

        h = hops_len
        for tip in user_tip_balances:
            amount: int = int(str(tip.amount))
            tip_fee = hop_fee_map[tip.denom]
            q = amount // tip_fee
            if q >= h:
                if str(tip.asset_class) == AssetClass.NATIVE_TOKEN.value:
                    fee = tip_fee * h
                    fee_redeem.append(NativeAsset(
                        str(tip.denom), str(fee)))
                    h = 0
                    break
            else:
                fee = tip_fee * q
                fee_redeem.append(NativeAsset(str(tip.denom), str(fee)))
                h = h - q
        err_msg = """tip_balance={} is not sufficient to pays for fees
                    based on hops_len={} and fees structure = {}""".format(user_tip_balances,
                                                                           hops_len, hop_fee_map)
        assert h == 0, err_msg

        return fee_redeem

    def build_hops(self, start_denom: str, target_denom: str, hops_len: int) -> List[AstroSwap]:
        db = Database()

        list_hops = db.get_whitelisted_hops_complete(
            start_denom, target_denom, hops_len)

        err_msg = """There is no hops with inputs:
                    start_denom={},
                    target_denom={},
                    hops_len={}""".format(start_denom, target_denom, hops_len)
        assert len(list_hops) > 0, err_msg

        # todo: Best execution = $ value of amount of out tokens I get - fees I pay for the bot that executed the dca
        # Current strategy: pick the first whitelisted hops
        hops_string = list_hops[0]["hops"]
        return parse_hops_from_string(hops_string, db.get_whitelisted_tokens(), db.get_whitelisted_hops())

    def purchase(self, order: DcaOrder):
        hops = self.build_hops(str(order.initial_asset_denom),
                               str(order.target_asset_denom),
                               order.max_hops.real)

        fee_redeem = self.build_fee_redeem(str(order.user_address),  len(hops))

        self.dca.execute_perform_dca_purchase(
            str(order.user_address), order.dca_order_id.real, hops, fee_redeem)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)

    terra = LocalTerra()

    db = Database()

    # res = db.get_dca_orders("terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
    # order = res[0]
    # for r in res:
    #     print(r)

    exec = ExecOrder()

    # exec.dca.query_get_user_dca_orders(
    #     "terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v")

    res = db.get_dca_orders("terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
    order = res[0]

    # db.get_user_tip_balance()
    # exec.purchase(order)

    # db.get_dca_orders("terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
    # order = res[0]
    # for r in res:
    #     print(r)

    # id = 1  # --> native target asset
    # id = 3  # --> token target asset
    # execute_purchase(user_address, id)

    # hops = build_hops("denom1", "denom2", 2)
    # print(hops)

    # hops = build_hops("denom1", "denom3", 2)
    # print(hops)

    # hops = build_hops(
    #    "terra1cyd63pk2wuvjkqmhlvp9884z4h89rqtn8w8xgz9m28hjd2kzj2cq076xfe", "uluna", 3)
    # print(len(hops))

    # hops = build_hops("terra1cyd63pk2wuvjkqmhlvp9884z4h89rqtn8w8xgz9m28hjd2kzj2cq076xfe",
    #                  "terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul", 3)
    # print(hops)
