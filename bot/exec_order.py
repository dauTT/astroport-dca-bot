import traceback
from bot.db.table.dca_order import DcaOrder
from bot.db.table.purchase_history import PurchaseHistory
from bot.type import AssetClass, TokenAsset, SimulateSwapOperation
from bot.util import AstroSwap, NativeAsset,\
    Asset, parse_hops_from_string
from typing import List, Optional
from bot.db.table.user_tip_balance import UserTipBalance
from bot.db_sync import Sync
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
import logging


logger = logging.getLogger(__name__)


class ExecOrder(Sync):
    """
    This is the main class of the bot application. It groups
    convenient methods for the execution of the dca orders
    """

    def __init__(self):
        super().__init__()

    def build_fee_redeem(self, user_address: str,  hops_len: int) -> List[Asset]:
        """ The bot will try to take fee from the first asset in user_tip_balance.
            If this is not sufficient, it will consider also the second asset and so on.
            For each hop the bot can take a fee amount as configured in whitelisted_fee_assets.
            If user_tip_balance is not sufficient to pay the fees for the bot, this method will throw an error.

            Parameters:
                - user_address (str): the address of the user.
                - hops_len (int): the number of hops (swap operations) between a start asset and the target asset.

            Returns:
                List[Asset]: list of Assets
                             - example: [Native('uluna', '1000'), TokenAsset('token_addrr', '2000' )]

        """

        def _get_asset(tip: UserTipBalance) -> Asset:
            fee_asset: Asset
            if str(tip.asset_class) == AssetClass.NATIVE_TOKEN.value:
                logger.debug("*** native ***")
                fee_asset = NativeAsset(str(tip.denom), str(fee))
                logger.debug(fee_asset.get_asset())
            else:
                logger.debug("*** token ***", )
                fee_asset = TokenAsset(str(tip.denom), str(fee))
                logger.debug(fee_asset.get_asset())
            return fee_asset

        logger.debug("build_fee_redeem")
        user_tip_balances = self.db.get_user_tip_balance(user_address)
        whitelisted_fee_assets = self.db.get_whitelisted_fee_asset()

        fee_redeem: List[Asset] = []
        hop_fee_map = {}
        for asset in whitelisted_fee_assets:
            hop_fee_map[asset.denom] = asset.amount.real
        assert len(user_tip_balances) > 0, "user_tip_balance is empty!"
        logger.debug("hop_fee_map={}".format(hop_fee_map))

        h = hops_len
        for tip in user_tip_balances:
            amount: int = tip.amount.real
            tip_fee = hop_fee_map[tip.denom]
            q = amount // tip_fee
            if q >= h:
                fee = tip_fee * h
                fee_redeem.append(_get_asset(tip))
                h = 0
                break
            else:
                fee = tip_fee * q
                fee_redeem.append(_get_asset(tip))
                h = h - q
        err_msg = """tip_balance={} is not sufficient to pays for fees
                    based on hops_len={} and fees structure = {}""".format(user_tip_balances,
                                                                           hops_len, hop_fee_map)
        assert h == 0, err_msg

        logger.debug("fee_redeem: {}".format(fee_redeem))
        return fee_redeem

    def build_fee_reedem_usd_map(self, user_address: str,  list_hops_string: List[str], prices: dict) -> dict:
        """
            Parameters:
                - user_address (str): the address of the user.
                - list_hops_string (List[str]): a list of hops string. 
                    A hops string identifies the hops to perform between a start asset and the target asset.
                    example: ['<1>', '<1><2>']
                - prices (dict): key = asset's denomination, value = price in usd
                    example: {'uluna': 0.1
                              'token_addr1': 0.2}

            returns:
                dict: key = hops_string, value = fee_redeem
                      example: { "<1>": 0.1,
                                 "<1><2>": 0.3 } 

        """

        logger.info("build_fee_reedem_usd_map")
        fee_redem_usd_map = {}
        hops_len = 0
        for h in list_hops_string:
            try:
                hops_len = len(h.split("><"))
                fee_reedem = self.build_fee_redeem(user_address, hops_len)
                fee_redem_usd_map[h] = self.convert_assets_to_usd_amount(
                    fee_reedem, prices)
            except:
                erro_msg = traceback.format_exc()
                logger.error("Unable to build fee_redeem for user_address={} with hop_len={}. err_msg={}".format(
                    user_address, hops_len, erro_msg
                ))

        assert fee_redem_usd_map != {
        }, "Unable to generate any fee_redem for the candidate list_hops={}".format(list_hops_string)

        logger.debug("fee_reedem_usd_map={}".format(fee_redem_usd_map))
        return fee_redem_usd_map

    def convert_assets_to_usd_amount(self, assets: List[Asset], prices: dict) -> float:
        """
            Parameters:
                - assets (List[Asset]): list of assets.
                    example: [Native('uluna', '1000'), TokenAsset('token_addrr', '2000' )]

                - prices (dict): key = asset's denomination, value = price in usd
                    example: {'uluna': 0.1
                              'token_addr1': 0.2}
            Returns:
                float: the usd value of the list of assets

        """
        total_usd_amount = 0
        for a in assets:
            amount = int(a.get_asset()["amount"])
            amount_usd = amount * prices[a.get_denom()]
            total_usd_amount += amount_usd
        return total_usd_amount

    def get_token_price_map(self) -> dict:
        """
            Returns:
                dict: key = asset's denomination, value = price in usd
                    example: {'uluna': 0.1
                             'token_addr1': 0.2} 
        """
        prices = {}
        for tp in self.db.get_token_price():
            if tp.price != None:
                price_per_one_unit = tp.price / tp.conversion.real
                prices[tp.denom] = price_per_one_unit
        return prices

    def build_hops(self, user_address: str,  offer_amount: int, start_denom: str,
                   target_denom: str, hops_len: int) -> List[AstroSwap]:
        """
            Parameters:
                - user_address (str): the address of the user.
                - offer_amount (int): the amount of the start asset
                - start_denom (str): the denomination of the start asset 
                - target_denom (str): the denomination of the target asset
                - hops_len (int): the number of hops (swap operations) between a start asset and the target asset.

            Returns:
                List[AstroSwap]: the hops (swap operations) between a start asset and the target asset
                - example: [AstroSwap(asset_info_start, asset_info_1), 
                           AstroSwap(asset_info_1, asset_info_2),
                           AstroSwap(asset_info_2, asset_info_target) ]

        """
        logger.info("build_hops:")

        list_hops = self.db.get_whitelisted_hops_all(
            start_denom, target_denom, hops_len)

        err_msg = """There are no hops with inputs:
                    start_denom={},
                    target_denom={},
                    hops_len={}""".format(start_denom, target_denom, hops_len)
        assert len(list_hops) > 0, err_msg

        list_hops_string = [h["hops"] for h in list_hops]
        prices = self.get_token_price_map()
        logger.debug("prices={}".format(prices))

        fee_redem_usd_map = self.build_fee_reedem_usd_map(
            user_address, list_hops_string, prices)

        best_hops_string = self.choose_best_execution_hop(target_denom,
                                                          offer_amount, fee_redem_usd_map, prices)

        return parse_hops_from_string(best_hops_string, self.db.get_whitelisted_tokens(), self.db.get_whitelisted_hops())

    def choose_best_execution_hop(self,  target_denom: str,
                                  offer_amount: int, fee_redem_usd_map: dict, prices: dict) -> str:
        """ 
            Choose the best hops string key in fee_redem_usd_map which provides the greatest execution value:
            execution = (simulated target token receive in usd) - (fee in usd)

            Parameters:
                - target_denom (str): the denomination of the target asset.
                - offer_amount (int): the amount of the start asset. 
                    (The start asset info is implicitly defined in the hops string keys of fee_redem_usd_map)
                - fee_redem_usd_map (dict): key = hops_string, value = fee redeem in usd
                    example: { "<1>": 0.1,
                                 "<3><2>": 0.3 } 
                - prices (dict): key = asset's denomination, value = price in usd
                    example: {'uluna': 0.1
                              'token_addr1': 0.2}

            Returns:
                - str: the hops string key in fee_redem_usd_map with the greatest execution value.
                    example: '<1><2>'

        """

        list_hops_string = list(fee_redem_usd_map.keys())
        logger.info(
            "choose best execution hop from this list: {}".format(list_hops_string))
        if len(list_hops_string) == 1:
            logger.info("best_hop: {}".format(list_hops_string[0]))
            return list_hops_string[0]

        best_hop = list_hops_string[0]
        best_execution = 0
        for hop in list_hops_string:
            try:
                hop_fees_usd_amount = fee_redem_usd_map[hop]
                swap_operations = parse_hops_from_string(
                    hop, self.db.get_whitelisted_tokens(), self.db.get_whitelisted_hops())
                swo = SimulateSwapOperation(offer_amount, swap_operations)
                target_token_receive = self.dca.simulate_swap_operations(swo)
                target_usd_amount = target_token_receive * prices[target_denom]
                hop_execution = target_usd_amount - hop_fees_usd_amount
                if hop_execution > best_execution:
                    best_execution = hop_execution
                    best_hop = hop
            except:
                erro_msg = traceback.format_exc()
                logger.error("Unable to calculate current hop={} execution amount. err_msg={}".format(
                    hop, erro_msg
                ))
        logger.info("best_hop={}".format(best_hop))
        return best_hop

    def purchase(self, order: DcaOrder):
        """ execute the dca order.
        """
        logger.info("""**************** Purchase Order *******************
            {}""".format(order))

        err_msg = ""
        success = True
        hops = []
        fee_redeem = []
        try:
            hops = self.build_hops(str(order.user_address),
                                   order.initial_asset_amount.real,
                                   str(order.initial_asset_denom),
                                   str(order.target_asset_denom),
                                   order.max_hops.real,
                                   )

            fee_redeem = self.build_fee_redeem(
                str(order.user_address),  len(hops))

            self.dca.execute_perform_dca_purchase(
                str(order.user_address), order.dca_order_id.real, hops, fee_redeem)
        except:
            err_msg = traceback.format_exc()
            # sometimes there may be an error (e.g timeout error.).
            # Nonetheless the purchase still went through.
            # So success field should not be interpret in the strict sense
            success = False

        self.db.log_purchase_history(str(order.id), int(str(order.initial_asset_amount)),
                                     str(order.initial_asset_denom), str(
                                         order.target_asset_denom),
                                     int(str(order.dca_amount)
                                         ),  "{}".format(hops),
                                     "{}".format([f.get_asset()
                                                 for f in fee_redeem]),
                                     success, err_msg)

    def purchase_and_sync(self, order_id: str, scheduler: Optional[BlockingScheduler] = None):
        """ execute the dca order, sync the local db and optionally re-schedule the next execution
        """
        try:
            orders = self.db.get_dca_orders(order_id)
            if len(orders) == 0:
                logger.info("oder_id={} does not exist!".format(order_id))

            assert len(
                orders) == 1, "Got multiple order with the same id: {}".format(orders)

            order = orders[0]
            user_address = str(order.user_address)
            self.purchase(order)
            self.sync_user_data(user_address)

            orders = self.db.get_dca_orders(
                user_address=user_address, schedule=False)
            if len(orders) == 0:
                logger.info("""Can't schedule next run time for order_id={1}.
                The order is either fully completed and removed from the dca_order table or
                the trigger 'reset_schedule' didn't work because something went wrong.
                Check this query to investigate further:

                select *
                from {0}
                where
                    success = 0
                    and order_id = '{1}'
                """.format(PurchaseHistory.__tablename__, order.id))
            if scheduler is not None and len(orders) > 0:
                self.schedule_next_run(orders, scheduler)
        except:
            err_msg = traceback.format_exc()
            calling_method = "purchase_and_sync"
            self.db.log_error(err_msg, calling_method, order_id)

    def schedule_next_run(self, orders: List[DcaOrder], scheduler: BlockingScheduler):
        """ It schedules for each order a one off purchase job to be executed at a future date.

            Parameters:
                - orders (List[DcaOrder]): a list of dca orders
                - scheduler (BlockingScheduler): a instance of BlockingScheduler which is responsible for
                    executing the schedule jobs.
        """

        delta = 20
        for order in orders:
            next_run_time = datetime.utcfromtimestamp(
                order.interval.real + order.last_purchase.real)
            if next_run_time < datetime.utcnow():
                next_run_time = datetime.utcnow() + timedelta(seconds=delta)
                delta += 60

            scheduler.add_job(self.purchase_and_sync, 'date',
                              run_date=next_run_time,  id=order.id,  args=[order.id, scheduler])

            logger.info(
                "update order_id={}: schedule=True, next_run_time={}".format(
                    order.id, next_run_time))
            order.schedule = True
            order.next_run_time = next_run_time
            self.db.insert_or_update(order)

    def schedule_orders(self, scheduler: BlockingScheduler):
        """ This method is basically like schedule_next_run but it does not depend
            on the orders arguments. It will be schedule to run on regular basis to pick
            up new orders which are not scheduled yet or orders with next_run_time expired.
        """
        orders = self.db.get_dca_orders(schedule=False)
        if len(orders) > 0:
            self.schedule_next_run(orders, scheduler)

        expired_next_run_time_orders = self.db.get_dca_orders(
            expired_next_run_time=True)
        if len(expired_next_run_time_orders) > 0:
            self.schedule_next_run(expired_next_run_time_orders, scheduler)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)
    # eo = ExecOrder()
    pass
