import pandas as pd
from pandas import DataFrame
from typing import Any
from bot.db.base import engine
from bot.db.table.dca_order import DcaOrder
from bot.db.table.user import User
from bot.db.table.dca_order import DcaOrder
from bot.db.table.whitelisted_token import WhitelistedToken
from bot.db.table.whitelisted_hop import WhitelistedHop
from bot.db.table.whitelisted_fee_asset import WhitelistedFeeAsset
from bot.db.table.user_tip_balance import UserTipBalance
from bot.db.table.purchase_history import PurchaseHistory
from bot.db.table.log_error import LogError


class DF():
    """ This class provide a nice interface to convert sqllite tables to pandas dataframe.
    """

    def read_sql(self, sql):
        return pd.read_sql(sql, engine.connect())

    @property
    def user(self):
        return self.read_sql(User.__tablename__)

    @property
    def dca_order(self):
        return self.read_sql(DcaOrder.__tablename__)

    @property
    def whitelisted_token(self):
        return self.read_sql(WhitelistedToken.__tablename__)

    @property
    def whitelisted_hop(self):
        return self.read_sql(WhitelistedHop.__tablename__)

    @property
    def whitelisted_fee_asset(self):
        return self.read_sql(WhitelistedFeeAsset.__tablename__)

    @property
    def user_tip_balance(self):
        return self.read_sql(UserTipBalance.__tablename__)

    @property
    def purchase_history(self):
        return self.read_sql(PurchaseHistory.__tablename__)

    @property
    def log_error(self):
        return self.read_sql(LogError.__tablename__)

    @staticmethod
    def convert_to_df(list_table_object: Any) -> DataFrame:
        if len(list_table_object) == 0:
            return DataFrame()

        row = list_table_object[0]
        cols = [c.name for c in row.__table__.columns]
        pk = [c.name for c in row.__table__.primary_key]
        tuplefied_list = [(getattr(item, col) for col in cols)
                          for item in list_table_object]

        return pd.DataFrame.from_records(tuplefied_list, index=pk, columns=cols)


if __name__ == "__main__":
    # d = DF()
    # print(d.purchase_history)
    # print(d.log_error)
    pass
