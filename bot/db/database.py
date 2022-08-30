from datetime import date

from bot.db.table.user import User
from bot.db.table.dca_order import DcaOrder
from bot.db.table.whitelisted_token import WhitelistedToken
from bot.db.table.whitelisted_hop import WhitelistedHop
from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
from bot.db.table.user_tip_balance import UserTipBalance
from bot.util import NativeAsset, TokenAsset, AssetInfo, AssetClass, Order, AstroSwap
from bot.db.base import session_factory, engine, Base
from sqlalchemy import exc, inspect, text, MetaData
from sqlalchemy.orm import scoped_session
from typing import Any, List
from functools import lru_cache
import json
import logging

logger = logging.getLogger(__name__)


# Generate database schema
# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
Session = scoped_session(session_factory)


def db_persist(func):
    def persist(*args, **kwargs):
        session = Session()
        try:
            func(*args, **kwargs)
            session.commit()
            logger.info("success calling db func: " + func.__name__)
        except exc.SQLAlchemyError as e:
            logger.error(e.args)
            session.rollback()
        finally:
            session.close()
    return persist


class Database:

    def get_tables_names(self):
        ins = inspect(engine)
        output = ins.get_table_names()
        logger.info([t for t in output])
        return output

    @db_persist
    def insert_or_update(self, table_object):
        session = Session()

        logger.debug("insert_or_update: table_object={}, {} ".format(
            table_object.__tablename__,
            ["{}={}".format(k, table_object.__dict__[k])
             for k in table_object.__dict__ if k != "_sa_instance_state"]))

        return session.merge(table_object)

    def drop_table(self, table: Any):
        """ :param table: the class which model the table in the database 
        """
        logger.info(f'Deleting {table.__tablename__} table')
        table.__table__.drop(engine)

    def query(self, table_object):
        session = Session()
        query = session.query(table_object)
        result = query.all()
        print("XXXXXXXXXXXX result: ")
        for r in result:
            print(r)

    def sql_query(self, query: str) -> List[dict]:
        sql = text(query)
        cursor = engine.execute(sql)
        result = [dict(zip(list(cursor.keys()), list(r)))
                  for r in cursor.fetchall()]

        logger.info("result: {}".format(json.dumps(result, indent=4)))
        return result

    def get_users(self) -> List[dict]:
        sql = "SELECT id FROM {}".format(User.__tablename__)
        return self.sql_query(sql)

    def get_dca_orders(self) -> List[dict]:
        columns = ['id', 'user_address', 'dca_order_id', 'token_allowance',
                   'initial_asset_class', 'initial_asset_denom', 'initial_asset_amount',
                   'target_asset_class', 'target_asset_denom', 'interval',
                   'last_purchase', 'dca_amount', 'max_spread', 'max_hop']
        sql = "SELECT {} FROM {}".format(
            ",".join(columns), DcaOrder.__tablename__)
        return self.sql_query(sql)

    def get_whitelisted_fee_asset(self) -> List[dict]:
        columns = ['denom', 'asset_class', "amount"]
        sql = "SELECT {} FROM {}".format(
            ",".join(columns),
            WhitelistedFeeAsset.__tablename__)
        return self.sql_query(sql)

    def get_user_tip_balance(self, user_address: str = ""):
        filter_user_address = "1 = 1" if user_address == "" else "user_id = '{}'".format(
            user_address)

        columns = ['id', 'user_id', 'denom', 'asset_class', 'amount']
        sql = "SELECT {} FROM {} WHERE {}".format(
            ",".join(columns),
            UserTipBalance.__tablename__,
            filter_user_address)
        return self.sql_query(sql)

    @lru_cache(maxsize=100)
    def get_whitelisted_tokens(self) -> List[dict]:
        columns = ['denom', 'asset_class']
        sql = "SELECT {} FROM {}".format(
            ",".join(columns), WhitelistedToken.__tablename__)
        return self.sql_query(sql)

    @lru_cache(maxsize=100)
    def get_whitelisted_hops(self):
        columns = ['id', 'pair_id', 'offer_denom', 'ask_denom']
        sql = "SELECT {} FROM {}".format(
            ",".join(columns), WhitelistedHop.__tablename__)
        return self.sql_query(sql)

    @lru_cache(maxsize=10, typed=True)
    def get_whitelisted_hops_complete(self, start_denom: str = "", target_denom: str = "", hops_len: int = 0) -> List[dict]:
        """ This view provide the complete list of hops (swap operations) that the bot can chose from.
        """
        def _filter_denom(col: str,  denom: str):
            return "1 = 1 " if denom == "" else "{} = '{}'".format(col, denom)
        filter_start_denom = _filter_denom("start_denom", start_denom)
        filter_target_denom = _filter_denom("target_denom", target_denom)
        filter_hops_len = "1 = 1" if hops_len == 0 else "hops_len <= {}".format(
            hops_len)

        sql = """
        WITH RECURSIVE
            cte(start_denom, id , hops_len, target_denom, hops) AS (
            SELECT
                offer_denom AS start_denom,
                CAST(id AS TEXT) AS id,
                1 AS hops_len,
                ask_denom as target_denom,
                '<' || CAST(id AS TEXT) || '>' AS hops
            FROM whitelisted_hop
            UNION ALL
            SELECT
                ask_denom AS start_denom,
                'inverse-' || CAST(id AS TEXT) AS id,
                1 AS hops_len,
                offer_denom as target_denom,
                '<inverse-' || CAST(id AS TEXT) || '>' AS hops
            FROM whitelisted_hop
            UNION ALL
            SELECT
                start_denom,
                CAST(wh.id AS TEXT) AS id,
                hops_len + 1 AS hops_len,
                wh.ask_denom,
                cte.hops ||  CASE WHEN cte.target_denom=wh.offer_denom
                                   THEN '<'
                                   ELSE '<inverse-'
                               END || CAST(wh.id AS TEXT) || '>' AS hops
            FROM cte
                JOIN whitelisted_hop AS wh ON (cte.target_denom=wh.offer_denom
                or cte.target_denom = wh.ask_denom
                ) and (cte.hops NOT LIKE '%<' || CAST(wh.id AS TEXT) || '>%'
                                            and cte.hops NOT LIKE '%<inverse-' || CAST(wh.id AS TEXT) || '>%')

        )
        SELECT
            start_denom,
            id ,
            hops_len,
            target_denom,
            hops
        FROM cte
        WHERE
            {}
            AND {}
            AND {} 
        """.format(filter_start_denom, filter_target_denom, filter_hops_len)
        return self.sql_query(sql)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)

    db = Database()
    u1 = User("123")
    u2 = User("1")
    db.insert_or_update(u1)
    db.insert_or_update(u2)

    o1: Order = {"id": 5,
                 "token_allowance": "10",
                 "initial_asset": TokenAsset("Token1", "1000"),
                 "target_asset": AssetInfo(AssetClass.TOKEN, "token2"),
                 "interval": 2,
                 "last_purchase": 500,
                 "dca_amount": "100",
                 }

    o2: Order = {"id": 6,
                 "token_allowance": "10",
                 "initial_asset": NativeAsset("uluna", "1000"),
                 "target_asset": AssetInfo(AssetClass.NATIVE_TOKEN, "token2"),
                 "interval": 2,
                 "last_purchase": 800,
                 "dca_amount": "1000",
                 }

    dcao1 = DcaOrder("1", '0.5', 2,  o1)
    dcao2 = DcaOrder("12", '0.6', 3, o2)

    o3: Order = {"id": 6,
                 "token_allowance": "10",
                 "initial_asset": NativeAsset("uluna", "1000"),
                 "target_asset": AssetInfo(AssetClass.NATIVE_TOKEN, "token2"),
                 "interval": 2,
                 "last_purchase": 1000,
                 "dca_amount": "1000",
                 }

    o4: Order = {"id": 6,
                 "token_allowance": "10",
                 "initial_asset": NativeAsset("uluna", "1000"),
                 "target_asset": AssetInfo(AssetClass.NATIVE_TOKEN, "token2"),
                 "interval": 2,
                 "last_purchase": 2000,
                 "dca_amount": "1000",
                 }

    dcao3 = DcaOrder("1", '0.3', 1,  o3)
    dcao4 = DcaOrder("12", '0.4', 2, o4)

    # print("XXXXXXXXXXXXXXXXX")
    # print(dcao1)
    db.insert_or_update(dcao1)
    db.insert_or_update(dcao2)
    db.insert_or_update(dcao3)
    db.insert_or_update(dcao4)

    # db.insert_or_update(DcaOrder("12999", o4))

    # query = "SELECT * FROM dca_order"
    # # query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    # db.sql_query(query)

    # query = "SELECT * FROM user"
    # # query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    # db.sql_query(query)

    # db.query(User)
    # db.query(DcaOrder)
    # db.get_users()
    # db.get_dca_orders()

    ai1 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom1")
    ai2 = AssetInfo(AssetClass.NATIVE_TOKEN, "denom2")
    ai3 = AssetInfo(AssetClass.TOKEN, "denom3")

    w1 = WhitelistedToken(ai1)
    w2 = WhitelistedToken(ai2)
    w3 = WhitelistedToken(ai3)

    db.insert_or_update(w1)
    db.insert_or_update(w2)
    db.insert_or_update(w3)

    db.get_whitelisted_tokens()

    # astro_swap1 = AstroSwap(ai1, ai2)
    # astro_swap2 = AstroSwap(ai2, ai3)
    # ws1 = WhitelistedHop(astro_swap1)
    # ws2 = WhitelistedHop(astro_swap2)
    # db.insert_or_update(ws1)
    # db.insert_or_update(ws2)

    db.get_whitelisted_hops()

    # db.get_tables_names()

    db.get_whitelisted_hops_complete()
    db.get_whitelisted_hops_complete("denom1", "denom3", 1)
    # db.get_whitelisted_hops_complete("denom1")

    # WhitelistedHop.__table__.drop(engine)
    # db.drop_table(WhitelistedHop)

    fee1 = NativeAsset("denom1", "100")
    fee2 = TokenAsset("denom2", "100")

    wfee1 = WhitelistedFeeAsset(fee1)
    wfee2 = WhitelistedFeeAsset(fee2)

    db.insert_or_update(wfee1)
    db.insert_or_update(wfee2)

    db.get_tables_names()

    db.get_whitelisted_fee_asset()

    utb1 = UserTipBalance("1", fee1)
    utb2 = UserTipBalance("1", fee2)

    db.insert_or_update(utb1)
    db.insert_or_update(utb2)

    db.get_user_tip_balance("1")
    db.get_dca_orders()

    # db.drop_table(DcaOrder)
