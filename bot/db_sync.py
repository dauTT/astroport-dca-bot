from multiprocessing import pool
from bot.db.database import Database
from bot.db.table.user_tip_balance import UserTipBalance
from bot.db.table.user import User
from bot.db.table.dca_order import DcaOrder
from bot.db.table.whitelisted_token import WhitelistedToken
from bot.db.table.whitelisted_hop import WhitelistedHop
from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
from dca import DCA
from terra_sdk.client.localterra import LocalTerra
from bot.util import AssetInfo, read_artifact, parse_dict_to_asset, \
    parse_dict_to_asset_info, parse_dict_to_order, AstroSwap
import logging
from typing import List
import json
logger = logging.getLogger(__name__)


class Sync:

    def __init__(self):
        self.cfg_dca = {}  # configuration of the dca contract
        self.network = read_artifact("localterra")
        self.terra = LocalTerra()
        self.dca = DCA(
            self.terra, self.terra.wallets["test1"], self.network["dcaAddress"])
        self.db = Database()

    def get_cfg_dca(self):
        if self.cfg_dca == {}:
            self.refresh_cfg_dca()
        return self.cfg_dca

    def set_cfg_dca(self, cfg_dca: dict):
        self.cfg_dca = cfg_dca

    def refresh_cfg_dca(self):
        cfg_dca = self.dca.query_get_config()
        self.set_cfg_dca(cfg_dca)

    def insert_user_into_db(self):
        u1 = User(self.terra.wallets["test1"].key.acc_address)
        u2 = User(self.terra.wallets["test2"].key.acc_address)
        u3 = User(self.terra.wallets["test3"].key.acc_address)

        self.db.insert_or_update(u1)
        self.db.insert_or_update(u2)
        self.db.insert_or_update(u3)

    def _sync_user_tip_balance(self, user_address: str,  user_tip_balances: List[dict]):
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
        user_order_ids = []
        # insert or update user order
        for o in orders:
            order = parse_dict_to_order(o)
            user_order_ids.append(DcaOrder.build_id(user_address, order.id))
            dca_oder = DcaOrder(user_address, max_spread, max_hops, order)
            self.db.insert_or_update(dca_oder)

        # remove orphan user oder
        self.db.delete(DcaOrder, (DcaOrder.user_address == user_address) & (  # type: ignore
            DcaOrder.id.not_in(user_order_ids)))  # type: ignore

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

        p = self.dca.get_astro_pools(self.network["factoryAddress"])
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
        cfg_dca = self.get_cfg_dca()
        cfg_user = self.dca.query_get_user_config(user_address)
        dca_oders = self.dca.query_get_user_dca_orders(user_address)
        max_spread = cfg_dca['max_spread'] if cfg_user['max_spread'] is None else cfg_user['max_spread']
        max_hops = cfg_dca['max_hops'] if cfg_user['max_hops'] is None else cfg_user['max_hops']

        self._sync_user_tip_balance(user_address, cfg_user["tip_balance"])
        self._sync_dca_oders(user_address, max_spread, max_hops, dca_oders)

    def sync_dca_cfg(self):
        """ This method will sync the dca contract configurations to the local db of the bot.
            We will schedule this method to run once a while but not as frequently as sync_user_data.
        """
        self.refresh_cfg_dca()
        cfg_dca = self.get_cfg_dca()

        self._sync_whitelisted_fee_asset(cfg_dca["whitelisted_fee_assets"])
        self._sync_whitelisted_token(cfg_dca["whitelisted_tokens"])
        self.sync_whitelisted_hop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)
    terra = LocalTerra()
    s = Sync()
    s.insert_user_into_db()
    s.db.get_tables_names()

    s.sync_dca_cfg()
    s.sync_user_data(terra.wallets["test1"].key.acc_address)

    # s.db.get_users()
    # s.db.get_user_tip_balance()
    # s.db.get_whitelisted_fee_asset()
    # s.db.get_whitelisted_tokens()
   # s.db.get_dca_orders()
    # s.db.get_whitelisted_hops()
    # s.db.get_whitelisted_hops_complete()
    s.db.get_user_tip_balance()

    # print(s.dca.query_get_user_dca_orders(
    #     terra.wallets["test1"].key.acc_address))
