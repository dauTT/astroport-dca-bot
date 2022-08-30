from sqlalchemy import Column, String, Integer, Date, ForeignKey

from bot.db.base import Base
from bot.db.table.user import User
from bot.util import Order


class DcaOrder(Base):
    __tablename__ = 'dca_order'

    id = Column(String, primary_key=True)
    user_address = Column(String, ForeignKey('user.id'))
    dca_order_id = Column(Integer)
    token_allowance = Column(String)
    initial_asset_class = Column(String)
    initial_asset_denom = Column(String)
    initial_asset_amount = Column(String)
    target_asset_class = Column(String)
    target_asset_denom = Column(String)
    interval = Column(Integer)
    last_purchase = Column(Integer)
    dca_amount = Column(String)
    max_spread = Column(String)
    max_hop = Column(Integer)

    def __init__(self, user_address: str, max_spread: str, max_hop: int,  order: Order):
        self.id = "{}-{}".format(user_address, order["id"])
        self.user_address = user_address
        self.dca_order_id = order["id"]
        self.token_allowance = order["token_allowance"]
        self.initial_asset_class = order["initial_asset"].get_info(
        ).asset_class.value
        self.initial_asset_denom = order["initial_asset"].get_denom()
        self.initial_asset_amount = order["initial_asset"].get_asset()[
            "amount"]
        self.target_asset_class = order["target_asset"].asset_class.value
        self.target_asset_denom = order["target_asset"].denom
        self.interval = order["last_purchase"]
        self.last_purchase = order["last_purchase"]
        self.dca_amount = order["dca_amount"]
        self.max_spread = max_spread
        self.max_hop = max_hop

    def __repr__(self) -> str:
        return """id={}, user_address={}, dca_order_id={},
                  token_allowance={}, initial_asset_class={},
                  initial_asset_denom={}, target_asset_class={},
                  target_asset_denom={}, interval={}, last_purchase={},
                  dca_amount={}, max_spread={}, max_hop={}
        """.format(self.id, self.user_address, self.dca_order_id,
                   self.token_allowance, self.initial_asset_class,
                   self.initial_asset_denom, self.target_asset_class,
                   self.target_asset_denom, self.interval, self.last_purchase,
                   self.dca_amount, self.max_spread, self.max_hop)
