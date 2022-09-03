import traceback
from bot.db.table.dca_order import DcaOrder
from bot.type import AssetClass
from bot.util import AstroSwap, NativeAsset,\
    Asset, parse_hops_from_string
from typing import List
from bot.db.database import Database
from bot.db_sync import Sync
import logging

logger = logging.getLogger(__name__)


class ExecOrder(Sync):

    def __init__(self):
        super().__init__()

    def build_fee_redeem(self, user_address: str,  hops_len: int) -> List[Asset]:
        """ The bot will try to take fee from the first asset in user_tip_balance.
            If this this is not sufficient it will will consider also the second asset and so on.
            For each hop the bot can take a fee amount as configured in whitelisted_fee_assets.
            If user_tip_balance is not sufficient to pay the fees for the bot, this method will throw an error.
        """
        logger.info("build_fee_redeem")
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

        logger.debug("fee_redeem: {}".format(fee_redeem))
        return fee_redeem

    def build_hops(self, start_denom: str, target_denom: str, hops_len: int) -> List[AstroSwap]:
        logger.info("build_hops")
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
        logger.info("""**************** Purchase Order *******************
            {}""".format(order))

        hops = self.build_hops(str(order.initial_asset_denom),
                               str(order.target_asset_denom),
                               order.max_hops.real)

        fee_redeem = self.build_fee_redeem(
            str(order.user_address),  len(hops))

        err_msg = ""
        success = True
        try:
            self.dca.execute_perform_dca_purchase(
                str(order.user_address), order.dca_order_id.real, hops, fee_redeem)
        except:
            err_msg = traceback.format_exc()
            success = False

        self.db.log_purchase_history(str(order.id), int(str(order.initial_asset_amount)),
                                     str(order.initial_asset_denom), str(
                                         order.target_asset_denom),
                                     int(str(order.dca_amount)
                                         ),  "{}".format(hops),
                                     "{}".format([f.get_asset()
                                                 for f in fee_redeem]),
                                     success, err_msg)

    def purchase_and_sync(self, order_id: str):
        orders = self.db.get_dca_orders(order_id)
        if len(orders) == 0:
            logger.info("oder_id={} does not exist!".format(order_id))

        assert len(
            orders) == 1, "Got multiple order with the same id: {}".format(orders)

        order = orders[0]
        user_address = order.user_address
        self.purchase(order)
        self.sync_user_data(user_address)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)

    # db = Database()

    # res = db.get_dca_orders("terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
    # order = res[0]
    # for r in res:
    #     print(r)

   # exec = ExecOrder()

    # exec.dca.query_get_user_dca_orders(
    #     "terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v")

    # res = db.get_dca_orders("terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
    # order = res[0]

    # db.get_user_tip_balance()
    # purchase_and_sync(order)

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
