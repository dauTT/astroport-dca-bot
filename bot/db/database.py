from datetime import date

from bot.db.table.user import User
from bot.db.table.dca_order import DcaOrder
from bot.db.table.whitelisted_tokens import WhitelistedToken
from bot.util import NativeAsset, TokenAsset, AssetInfo, AssetClass, Order
from bot.db.base import session_factory, engine, Base
from sqlalchemy import exc, inspect, text
from sqlalchemy.orm import scoped_session

import logging

logger = logging.getLogger(__name__)


# Generate database schema
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
        for _t in ins.get_table_names():
            print("inspect: ", _t)

    @db_persist
    def insert_or_update(self, table_object):
        session = Session()

        logger.debug("insert_or_update: table_object={}, {} ".format(
            table_object.__tablename__,
            ["{}={}".format(k, table_object.__dict__[k])
             for k in table_object.__dict__ if k != "_sa_instance_state"]))

        return session.merge(table_object)

    def query(self, table_object):
        session = Session()
        query = session.query(table_object)
        result = query.all()
        print("XXXXXXXXXXXX result: ")
        for r in result:
            print(r)

    def sql_query(self, query: str):
        sql = text(query)
        cursor = engine.execute(sql)
        result = [dict(zip(list(cursor.keys()), list(r)))
                  for r in cursor.fetchall()]
        logger.info("result: {}".format(result))
        return result

    def get_users(self):
        sql = "SELECT id FROM {}".format(User.__tablename__)
        return self.sql_query(sql)

    def get_dca_orders(self):
        columns = ['id', 'user_address', 'dca_order_id', 'token_allowance', 'initial_asset_class', 'initial_asset_denom',
                   'initial_asset_amount', 'target_asset_class', 'target_asset_denom', 'interval', 'last_purchase', 'dca_amount']
        sql = "SELECT {} FROM {}".format(
            ",".join(columns), DcaOrder.__tablename__)
        return self.sql_query(sql)

    def get_whitelisted_tokens(self):
        columns = ['denom', 'asset_class']
        sql = "SELECT {} FROM {}".format(
            ",".join(columns), WhitelistedToken.__tablename__)
        return self.sql_query(sql)

    # print("\n", record)
    #
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.INFO)

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

    dcao1 = DcaOrder("1", o1)
    dcao2 = DcaOrder("12", o2)

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

    # print("XXXXXXXXXXXXXXXXX")
    # print(dcao1)
    # db.insert_or_update(dcao1)
    # db.insert_or_update(dcao2)
    # db.insert_or_update(DcaOrder("12", o3))
    # db.insert_or_update(DcaOrder("12", o4))

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
    ai3 = AssetInfo(AssetClass.TOKEN, "tokne_contract1")

    w1 = WhitelistedToken(ai1)
    w2 = WhitelistedToken(ai2)
    w3 = WhitelistedToken(ai3)

    db.insert_or_update(w1)
    db.insert_or_update(w2)
    db.insert_or_update(w3)

    db.get_whitelisted_tokens()
