from sqlalchemy import Column, String, Integer, Date
from bot.db.base import Base
from bot.type import Asset, AssetClass


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
        repr = ["{}={}".format(k, self.__dict__[k])
                for k in self.__dict__.keys() if k != "_sa_instance_state"]
        nice_string = """
    """.join(repr)
        return """[
    {}
]""".format(nice_string)
