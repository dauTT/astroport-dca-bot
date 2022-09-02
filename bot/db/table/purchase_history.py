from xmlrpc.client import Boolean
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, Boolean
from bot.db.base import Base
from bot.type import Order
from bot.db.table import row_string
from datetime import datetime


class PurchaseHistory(Base):
    """
        We track the purchase order history as long as the order is relevant.
        Once a user order is complete, the corresponding purchasse history will be also deleted.
        Column hops, success and err_msd are especially important
    """
    __tablename__ = 'purchase_history'

    id = Column(Integer, primary_key=True)
    create_at = Column(DateTime, default=datetime.now())
    order_id = Column(String, ForeignKey("dca_order.id", ondelete="CASCADE"))
    dca_amount = Column(Integer, nullable=False)
    # The actually hops which the bot has chosen to execute the purchase
    # of the target asset
    hops = Column(String, nullable=False)
    fee_reedem = Column(String, nullable=False)
    # This flag indicates whether the purchase for successfull or not.
    success = Column(Boolean, nullable=False)
    # If the purhcase was not successfull, the bot will report a err_msg
    err_msg = Column(String)

    def __init__(self, order_id: str,  dca_amount: int, hops: str, fee_reedem, success: bool, err_msg: str):
        self.order_id = order_id
        self.dca_amount = dca_amount
        self.hops = hops
        self.fee_reedem = fee_reedem
        self.success = success
        self.err_msg = err_msg

    def __repr__(self) -> str:
        return row_string(self)