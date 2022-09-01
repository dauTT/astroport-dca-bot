from sqlalchemy import Column, String, Integer, ForeignKey
from bot.db.base import Base
from bot.type import Order


class DcaOrder(Base):
    __tablename__ = 'dca_order'

    id = Column(String, primary_key=True)
    user_address = Column(String, ForeignKey('user.id'))
    dca_order_id = Column(Integer, nullable=False)
    token_allowance = Column(String)
    initial_asset_class = Column(String, nullable=False)
    initial_asset_denom = Column(String, nullable=False)
    initial_asset_amount = Column(String, nullable=False)
    target_asset_class = Column(String, nullable=False)
    target_asset_denom = Column(String, nullable=False)
    interval = Column(Integer, nullable=False)
    last_purchase = Column(Integer)
    dca_amount = Column(String, nullable=False)
    max_spread = Column(String, nullable=False)
    max_hops = Column(Integer, nullable=False)

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

    @staticmethod
    def build_id(user_address: str, order_id: int):
        return "{}-{}".format(user_address, order_id)

    def __repr__(self) -> str:
        repr = ["{}={}".format(k, self.__dict__[k])
                for k in self.__dict__.keys() if k != "_sa_instance_state"]
        nice_string = """
    """.join(repr)
        return """[
    {}
]""".format(nice_string)
