from sqlalchemy import Column, String, Integer, Date, ForeignKey
from bot.db.base import Base
from bot.util import Asset, AssetClass


class UserTipBalance(Base):
    __tablename__ = 'user_tip_balance'

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey(
        "user.id", ondelete="CASCADE"))
    denom = Column(String, primary_key=True)
    asset_class = Column(String, nullable=False)
    amount = Column(String, nullable=False)

    def __init__(self, user_address: str, asset: Asset):
        self.id = "{}-{}".format(user_address, asset.get_denom())
        self.user_id = user_address
        self.denom = asset.get_denom()
        self.asset_class = AssetClass.NATIVE_TOKEN.value if asset.is_native(
        ) else AssetClass.TOKEN.value
        self.amount = asset.get_asset()["amount"]

    def __repr__(self) -> str:
        return "denom={}, asset_class={}, amount={}".format(self.id, self.asset_class, self.amount)
