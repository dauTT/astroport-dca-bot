
from sqlalchemy import Column, String, Integer, Date, Identity, ForeignKey, UniqueConstraint
from bot.db.base import Base
from bot.util import AssetInfo, AstroSwap


class WhitelistedHop(Base):
    """ This class model the whitelisted hop (swap pair) which the bot can perform
    """
    __tablename__ = 'whitelisted_hop'

    # The id column is actually not necessary.
    # But is nice to have for recursively finding all the possibles hop combinations.
    id = Column(Integer, Identity(start=1, increment=1), primary_key=True)
    pair_id = Column(String)
    offer_denom = Column(String, ForeignKey(
        "whitelisted_token.denom", ondelete="CASCADE"))
    ask_denom = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint('pair_id'), )

    def __init__(self, astro_swap: AstroSwap):
        l = [astro_swap.offer_asset_info.denom,
             astro_swap.ask_asset_info.denom]
        l.sort()
        # By sorting l we ensure that the pair_id field is unique. This means that
        # AstroSwap(A,B) or AstroSwap(B,A) define the same hop.
        self.pair_id = "-".join(l)
        self.offer_denom = astro_swap.offer_asset_info.denom
        self.ask_denom = astro_swap.ask_asset_info.denom

    def __repr__(self) -> str:
        return "id={}, pair_id={}, offer_denom={}, ask_denom={}".format(self.id, self.pair,  self.offer_denom, self.ask_denom)
