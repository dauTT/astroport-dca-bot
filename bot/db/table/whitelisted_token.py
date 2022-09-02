from sqlalchemy import Column, String, Integer, Date
from bot.db.base import Base
from bot.type import AssetInfo
from bot.db.table import row_string


class WhitelistedToken(Base):
    __tablename__ = 'whitelisted_token'

    denom = Column(String, primary_key=True)
    asset_class = Column(String, nullable=False)

    def __init__(self, asset_info: AssetInfo):
        self.denom = asset_info.denom
        self.asset_class = asset_info.asset_class.value

    def __repr__(self) -> str:
        return row_string(self)
