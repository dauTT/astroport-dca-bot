from sqlalchemy import Column, String
from bot.db.base import Base
from bot.type import Asset, AssetClass
from bot.db.table import row_string


class WhitelistedFeeAsset(Base):
    __tablename__ = 'whitelisted_fee_asset'

    denom = Column(String, primary_key=True)
    asset_class = Column(String, nullable=False)
    amount = Column(String, nullable=False)

    def __init__(self, asset: Asset):
        self.denom = asset.get_denom()
        self.asset_class = AssetClass.NATIVE_TOKEN.value if asset.is_native(
        ) else AssetClass.TOKEN.value
        self.amount = asset.get_asset()["amount"]

    def __repr__(self) -> str:
        return row_string(self)
