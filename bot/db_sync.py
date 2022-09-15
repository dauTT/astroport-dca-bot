import os
from terra_sdk.core import Coins
from terra_sdk.client.localterra import LocalTerra
from terra_sdk.client.lcd import LCDClient
from bot.util import AssetInfo, parse_dict_to_asset, \
    parse_dict_to_asset_info, parse_dict_to_order, AstroSwap,\
    get_price
from typing import List
import json
import traceback
from terra_sdk.key.mnemonic import MnemonicKey
from bot.db.table.user_tip_balance import UserTipBalance
from bot.db.table.user import User
from bot.db.table.dca_order import DcaOrder
from bot.db.table.whitelisted_token import WhitelistedToken
from bot.db.table.whitelisted_hop import WhitelistedHop
from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
from bot.db.table.token_price import TokenPrice
from bot.db.table.log_error import LogError
from bot.db.table.purchase_history import PurchaseHistory
from bot.db.database import Database, create_database_objects, \
    drop_database_objects
from bot.settings import LCD_URL, CHAIN_ID, GAS_PRICE,\
    GAS_ADJUSTMENT, MNEMONIC, DCA_CONTRACT_ADDR, TOKEN_INFO
from bot.dca import DCA
import logging


logger = logging.getLogger(__name__)


class Sync:

    def __init__(self):
        terra = LCDClient(LCD_URL, CHAIN_ID,   Coins(  # type: ignore
            GAS_PRICE), GAS_ADJUSTMENT)  # type: ignore
        mk = MnemonicKey(mnemonic=MNEMONIC)

        self.dca = DCA(terra, terra.wallet(mk), DCA_CONTRACT_ADDR)
        self.db = Database()
        self.cfg_dca = {}  # configuration of the dca contract

    def get_cfg_dca(self):
        if self.cfg_dca == {}:
            self.refresh_cfg_dca()
        return self.cfg_dca

    def set_cfg_dca(self, cfg_dca: dict):
        self.cfg_dca = cfg_dca

    def refresh_cfg_dca(self):
        cfg_dca = self.dca.query_get_config()
        self.set_cfg_dca(cfg_dca)

    def insert_user_into_db(self, user_address: str):
        u = User(user_address)
        self.db.insert_or_update(u)

    def fill_token_price_table(self):
        for denom in TOKEN_INFO.keys():
            coingecko = TOKEN_INFO[denom]["coingecko"]
            tp = TokenPrice(
                denom, coingecko["id"], coingecko["symbol"], TOKEN_INFO[denom]["conversion"])
            self.db.insert_or_update(tp)

    def sync_token_price(self):
        list_token_price = self.db.get_token_price()
        if not (list_token_price):
            self.fill_token_price_table()
            list_token_price = self.db.get_token_price()

        coingecko_ids = ",".join([str(t.coingecko_id)
                                  for t in list_token_price])
        prices = get_price(coingecko_ids)

        logger.debug("prices={}".format(prices))
        for tp in list_token_price:
            price = prices.get(str(tp.coingecko_id), None)
            if price != None:
                tp.price = price["usd"]
                self.db.insert_or_update(tp)

    def initialize_token_price_table(self):
        self.fill_token_price_table()
        self.sync_token_price()

    def _sync_user_tip_balance(self, user_address: str,  user_tip_balances: List[dict]):
        logger.debug("_sync_user_tip_balance")
        user_tip_ids = []
        # insert or update user tip
        for a in user_tip_balances:
            asset = parse_dict_to_asset(a)
            user_tip_ids.append(UserTipBalance.build_id(
                user_address, asset.get_denom()))
            utb = UserTipBalance(user_address, asset)
            self.db.insert_or_update(utb)

        # remove orphan user tip
        self.db.delete(UserTipBalance, (UserTipBalance.user_address == user_address) & (  # type: ignore
            UserTipBalance.id.not_in(user_tip_ids)))  # type: ignore

    def _sync_dca_oders(self, user_address: str, max_spread: str, max_hops: int, orders: List[dict]):
        logger.debug("_sync_dca_oders")
        new_order_ids = []
        # insert or update user order
        for o in orders:
            order = parse_dict_to_order(o)
            new_order_ids.append(DcaOrder.build_id(user_address, order.id))
            dca_oder = DcaOrder(user_address, max_spread, max_hops, order)

            # update dca_order
            self.db.insert_or_update(dca_oder)
            # Note: there is a trigger 'reset_schedule' on the the dca_orders
            # which will reset schedule=False and next_run_time=NULL only if
            # new.initial_asset_amount < old.initial_asset_amount

        # remove orphan user oder
        self.db.delete(DcaOrder, (DcaOrder.user_address == user_address) & (  # type: ignore
            DcaOrder.id.not_in(new_order_ids)))  # type: ignore

    def _sync_whitelisted_fee_asset(self, whitelisted_fee_assets: List[dict]):

        wl_fee_assets_denom = []
        # insert or update whitelisted fee assets
        for a in whitelisted_fee_assets:
            asset = parse_dict_to_asset(a)
            wl_fee_assets_denom.append(asset.get_denom())
            wfa = WhitelistedFeeAsset(asset)
            self.db.insert_or_update(wfa)

        # remove orphan whitelisted fee assets
        self.db.delete(WhitelistedFeeAsset,
                       (WhitelistedFeeAsset.denom.not_in(wl_fee_assets_denom)))  # type: ignore

    def _sync_whitelisted_token(self, whitelisted_tokens: List[dict]):
        wl_tokens_denom = []
        # insert or update whitelisted tokens
        for a in whitelisted_tokens:
            asset_info = parse_dict_to_asset_info(a)
            wl_tokens_denom.append(asset_info.denom)
            wt = WhitelistedToken(asset_info)
            self.db.insert_or_update(wt)

        # remove orphan whitelisted fee assets
        self.db.delete(WhitelistedToken,
                       (WhitelistedToken.denom.not_in(wl_tokens_denom)))  # type: ignore

    def sync_whitelisted_hop(self):
        """ this method need to run typically after sync_whitelisted_token!
        """

        whitelisted_tokens_denom = [w.denom
                                    for w in self.db.get_whitelisted_tokens()]

        def is_whitelisted_asset(asset_info: AssetInfo) -> bool:
            return whitelisted_tokens_denom.__contains__(asset_info.denom)

        p = self.dca.get_astro_pools()
        logger.debug(
            "dca.get_astro_pools -> result: {}".format(json.dumps(p, indent=4)))

        wl_hops_pair_id = []
        # insert or update whitelisted hop
        for pair in p["pairs"]:
            asset_infos = pair["asset_infos"]
            asset1 = parse_dict_to_asset_info(asset_infos[0])
            asset2 = parse_dict_to_asset_info(asset_infos[1])
            if not (is_whitelisted_asset(asset1)):
                continue
            if not (is_whitelisted_asset(asset2)):
                continue
            astro_swap = AstroSwap(asset1, asset2)
            wl_hops_pair_id.append(WhitelistedHop.build_pair_id(astro_swap))
            wh = WhitelistedHop(astro_swap)
            self.db.insert_or_update(wh)

        # remove orphan whitelisted hop
        self.db.delete(WhitelistedHop,
                       (WhitelistedHop.pair_id.not_in(wl_hops_pair_id)))  # type: ignore

    def sync_user_data(self, user_address):
        """ This method will sync the user oders and tip balances to the local db of the bot.
            We will schedule this method to run frequently.
        """
        logger.info(
            "****** sync_user_data: user={} ******".format(user_address))

        try:
            cfg_dca = self.get_cfg_dca()
            cfg_user = self.dca.query_get_user_config(user_address)
            dca_oders = self.dca.query_get_user_dca_orders(user_address)
            max_spread = cfg_dca['max_spread'] if cfg_user['max_spread'] is None else cfg_user['max_spread']
            max_hops = cfg_dca['max_hops'] if cfg_user['max_hops'] is None else cfg_user['max_hops']

            self._sync_user_tip_balance(user_address, cfg_user["tip_balance"])
            self._sync_dca_oders(user_address, max_spread, max_hops, dca_oders)

            # update sync_data=True of the user
            self.db.insert_or_update(User(user_address, True))
        except:
            err_msg = traceback.format_exc()
            self.db.log_error(err_msg, "sync_user_data", "", user_address)

    def sync_users_data(self):
        logger.info("************ sync_users_data ************")
        users = self.db.get_users(sync_data=False)
        for u in users:
            self.sync_user_data(u.id)

    def sync_dca_cfg(self):
        """ This method will sync the dca contract configurations to the local db of the bot.
            We will schedule this method to run once a while but not as frequently as sync_user_data.
        """
        logger.info("************ sync_dca_cfg ************")
        try:
            self.refresh_cfg_dca()
            cfg_dca = self.get_cfg_dca()

            self._sync_whitelisted_fee_asset(cfg_dca["whitelisted_fee_assets"])
            self._sync_whitelisted_token(cfg_dca["whitelisted_tokens"])
            self.sync_whitelisted_hop()
        except:
            err_msg = traceback.format_exc()
            self.db.log_error(err_msg, "sync_dca_cfg")


def initialize_db(reset_db: bool = False):
    """
        Parameters:
            - reset_db (bool): this flag is responsible for dropping all objects in the database.                
    """
    DCA_BOT = os.environ['DCA_BOT']
    logger.info(
        "*************** ENVIRONMENT: {} **********************".format(
            DCA_BOT))
    logger.info("initialize_db:")

    assert DCA_BOT in [
        'dev', 'prod', 'test'], "Expected environment variable DCA_BOT in ['dev','prod', 'test']. Got DCA_BOT={}".format(DCA_BOT)

    if reset_db:
        drop_database_objects()

    create_database_objects()
    s = Sync()

    # insert some initial user into db
    if DCA_BOT == "dev":
        terra = LocalTerra()

        u1 = terra.wallets["test1"].key.acc_address
        u2 = terra.wallets["test2"].key.acc_address
        u3 = terra.wallets["test3"].key.acc_address

        s.insert_user_into_db(u1)
        s.insert_user_into_db(u2)
        s.insert_user_into_db(u3)

    elif DCA_BOT == "prod":
        # insert some dca user address here: ...
        # s.insert_user_into_db(...)
        pass
    else:  # DCA_BOT == "test":
        # insert some dca user address here: ...
        # s.insert_user_into_db(...)
        pass

    s.sync_dca_cfg()
    s.sync_users_data()
    s.initialize_token_price_table()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)
    # from bot.db.database import create_database_objects, drop_database_objects
    # drop_database_objects()
    # create_database_objects()
    # initialize_db()
    # s = Sync()
    pass
