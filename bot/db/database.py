from bot.db.table.user import User
from bot.db.table.dca_order import DcaOrder
from bot.db.table.whitelisted_token import WhitelistedToken
from bot.db.table.whitelisted_hop import WhitelistedHop
from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
from bot.db.table.user_tip_balance import UserTipBalance
from bot.db.table.purchase_history import PurchaseHistory
from bot.db.view.whitelisted_hops_all import create_or_alter_view, drop_view
from bot.db.table.log_error import LogError
from bot.db.base import session_factory, engine, Base
from sqlalchemy import exc, inspect, text, delete
from sqlalchemy.orm import scoped_session
from bot.db.pd_df import DF
from typing import Any, List, Optional
from functools import lru_cache
import json
import logging


logger = logging.getLogger(__name__)


def create_database_objects():
    Base.metadata.create_all(bind=engine)
    create_or_alter_view()


def drop_database_objects():
    drop_view()
    Base.metadata.drop_all(bind=engine)


# drop_database_objects()
create_database_objects()
Session = scoped_session(session_factory)


def db_persist(func):
    def persist(*args, **kwargs):
        session = Session()
        try:
            func(*args, **kwargs)
            session.commit()
            logger.debug("success calling db func: " + func.__name__)
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
    def insert_or_update(self, table_object: Any):
        session = Session()
        session.merge(table_object)

    @ db_persist
    def delete(self, table_object, filter: Any):
        session = Session()
        stmt = delete(table_object).where(filter)
        session.execute(stmt)

    @ db_persist
    def log_purchase_history(self, order_id: str, initial_amount: int,
                             initial_denom: str, target_denom: str,
                             dca_amount: int, hops: str, fee_redeem: str,
                             success: bool, err_msg: str):
        logger.info("log_purchase_history")

        session = Session()
        ph = PurchaseHistory(order_id, initial_amount, initial_denom,
                             target_denom, dca_amount, hops,
                             fee_redeem, success, err_msg)
        session.add(ph)

    @ db_persist
    def log_error(self, err_msg: str, calling_method: str, order_id: str = "", user_address: str = ""):
        logger.error("calling_method={}, order_id={}, user_address={}, err_msg={}".format(
            calling_method, order_id, user_address, err_msg))
        session = Session()
        le = LogError(order_id, user_address, calling_method, err_msg)
        session.add(le)

    def drop_table(self, table: Any):
        """ :param table: the class which model the table in the database
        """
        logger.info(f'Deleting {table.__tablename__} table')
        table.__table__.drop(engine)

    def query(self, table_object, filters: List[Any] = []):
        session = Session()
        query = session.query(table_object)
        for f in filters:
            query = query.filter(f)

        result = query.all()

        session.expunge_all()
        logger.debug("result query table: {}, filters={}: {}".format(
            table_object.__tablename__,
            filters, result))
        return result

    def sql_query(self, query: str) -> List[dict]:
        sql = text(query)
        cursor = engine.execute(sql)
        result = [dict(zip(list(cursor.keys()), list(r)))
                  for r in cursor.fetchall()]

        logger.debug("result: {}".format(
            json.dumps(result, indent=2)))
        return result

    def exec_sql(self, sql: str):
        sql_formatted = text(sql)
        engine.execute(sql_formatted)

    def get_users(self, sync_data: Optional[bool] = None) -> List[User]:
        filters = [] if sync_data is None else [User.sync_data == sync_data]
        return self.query(User, filters)

    def get_dca_orders(self, id: Optional[str] = None,  user_address: Optional[str] = None, schedule: Optional[bool] = None) -> List[DcaOrder]:
        """
            :params str id: the identifier od the order which is a contatenation of
                            the user address and the dca contract order id.
                            example: id=terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-123
        """
        filters = [] if id == None else [DcaOrder.id == id]
        if user_address != None:
            filters.append(DcaOrder.user_address == user_address)
        if schedule != None:
            filters.append(DcaOrder.schedule == schedule)

        return self.query(DcaOrder, filters)

    def get_purchase_history(self,  order_id: Optional[str] = None) -> List[PurchaseHistory]:
        filters = [] if order_id == None else [
            PurchaseHistory.order_id == order_id]
        return self.query(PurchaseHistory, filters)

    def get_user_tip_balance(self, user_address: Optional[str] = None) -> List[UserTipBalance]:
        filters = [] if user_address == None else [
            UserTipBalance.user_address == user_address]
        return self.query(UserTipBalance, filters)

    def get_log_error(self, order_id: Optional[str] = None, user_address: Optional[str] = None):
        filters = [] if order_id == None else [
            LogError.order_id == order_id]
        if user_address != None:
            filters.append(LogError.user_address == user_address)
        return self.query(LogError, filters)

    def get_whitelisted_fee_asset(self) -> List[WhitelistedFeeAsset]:
        return self.query(WhitelistedFeeAsset)

    # @lru_cache(maxsize=10)
    def get_whitelisted_tokens(self) -> List[WhitelistedToken]:
        return self.query(WhitelistedToken)

    # @lru_cache(maxsize=10)
    def get_whitelisted_hops(self) -> List[WhitelistedHop]:
        return self.query(WhitelistedHop)

    # @lru_cache(maxsize=10, typed=True)
    def get_whitelisted_hops_all(self, start_denom: str = "", target_denom: str = "", hops_len: int = 0) -> List[dict]:
        """ This view provide the complete list of hops (swap operations) that the bot can chose from.
        """
        def _filter_denom(col: str,  denom: str):
            return "1 = 1 " if denom == "" else "{} = '{}'".format(col, denom)
        filter_start_denom = _filter_denom("start_denom", start_denom)
        filter_target_denom = _filter_denom("target_denom", target_denom)
        filter_hops_len = "1 = 1" if hops_len == 0 else "hops_len <= {}".format(
            hops_len)

        sql = """
        SELECT
            start_denom,
            id ,
            hops_len,
            target_denom,
            hops
        FROM whitelisted_hops_all
        WHERE
            {}
            AND {}
            AND {}
        """.format(filter_start_denom, filter_target_denom, filter_hops_len)
        return self.sql_query(sql)

    @staticmethod
    def get_pd_df():
        return DF()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)

    # db = Database()
    # db.get_tables_names()
    pass
