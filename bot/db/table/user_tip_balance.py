from sqlalchemy import Column, String, ForeignKey, Integer
from bot.db.base import Base
from bot.type import Asset, AssetClass
from bot.db.table import row_string


class UserTipBalance(Base):
    __tablename__ = 'user_tip_balance'

    id = Column(String, primary_key=True)
    user_address = Column(String, ForeignKey(
        "user.id", ondelete="CASCADE"))
    denom = Column(String, primary_key=True)
    asset_class = Column(String, nullable=False)
    amount = Column(String, nullable=False)

    def __init__(self, user_address: str, asset: Asset):
        self.id = UserTipBalance.build_id(user_address, asset.get_denom())
        self.user_address = user_address
        self.denom = asset.get_denom()
        self.asset_class = AssetClass.NATIVE_TOKEN.value if asset.is_native(
        ) else AssetClass.TOKEN.value
        self.amount = asset.get_asset()["amount"]

    @staticmethod
    def build_id(user_address: str, denom: str):
        return "{}-{}".format(user_address, denom)

    def __repr__(self) -> str:
        return row_string(self)
