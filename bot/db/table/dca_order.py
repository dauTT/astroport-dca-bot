from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, event, \
    DDL, DateTime
from bot.db.base import Base
from bot.type import Order
from bot.db.table import row_string
from datetime import datetime


class DcaOrder(Base):
    __tablename__ = 'dca_order'

    id = Column(String, primary_key=True)
    user_address = Column(String, ForeignKey('user.id'))
    dca_order_id = Column(Integer, nullable=False)
    token_allowance = Column(Integer)
    initial_asset_class = Column(String, nullable=False)
    initial_asset_denom = Column(String, nullable=False)
    initial_asset_amount = Column(Integer, nullable=False)
    target_asset_class = Column(String, nullable=False)
    target_asset_denom = Column(String, nullable=False)
    interval = Column(Integer, nullable=False)
    last_purchase = Column(Integer)
    dca_amount = Column(Integer, nullable=False)
    max_spread = Column(String, nullable=False)
    max_hops = Column(Integer, nullable=False)

    # schedule column is True (=1) when the order is scheduled to be
    # executed by the bot. It is False (=0) when the bot has not yet schedule
    # it to be executed. By default new order have value False.
    # After every purchase this flag will be reset to False again.
    schedule = Column(Boolean, nullable=False, default=False)
    # next_run_time column store the next execution time of the order.
    # It is set to be some future time (typically greater than last_purchase + interval)
    # if schedule=True.
    next_run_time = Column(DateTime)

    def __init__(self, user_address: str, max_spread: str, max_hops: int,  order: Order):
        self.id = DcaOrder.build_id(user_address, order.id)
        self.user_address = user_address
        self.dca_order_id = order.id
        self.token_allowance = order.token_allowance
        self.initial_asset_class = order.initial_asset.get_info(
        ).asset_class.value
        self.initial_asset_denom = order.initial_asset.get_denom()
        self.initial_asset_amount = int(order.initial_asset.get_asset()[
            "amount"])
        self.target_asset_class = order.target_asset.asset_class.value
        self.target_asset_denom = order.target_asset.denom
        self.interval = order.interval
        self.last_purchase = order.last_purchase
        self.dca_amount = order.dca_amount
        self.max_spread = max_spread
        self.max_hops = max_hops

    def set_schedule(self, flag: bool):
        self.schedule = flag

    def set_next_run_time(self, date_time: datetime):
        self.next_run_time = date_time

    @staticmethod
    def build_id(user_address: str, order_id: int):
        return "{}-{}".format(user_address, order_id)

    def __repr__(self) -> str:
        return row_string(self)


# After each successful purchase we expect the initial_asset_amount to decrese.
# In this case the schedule flag will be reset to 0
reset_schedule = DDL("""
CREATE TRIGGER reset_schedule AFTER UPDATE ON dca_order
BEGIN
      UPDATE dca_order
        SET schedule = 0, next_run_time = NULL
      WHERE  id = new.id 
            AND (new.initial_asset_amount < old.initial_asset_amount) ;
END
  """)
event.listen(DcaOrder.__table__, 'after_create', reset_schedule)
