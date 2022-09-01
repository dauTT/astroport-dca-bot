
from sqlalchemy.schema import DDL
from sqlalchemy import Column, String, Integer, ForeignKey
from bot.db.base import Base
from bot.type import AstroSwap
from sqlalchemy import event, DDL


class WhitelistedHop(Base):
    """ This class model the whitelisted hop (swap pair) which the bot can perform
    """
    __tablename__ = 'whitelisted_hop'

    # The id column is actually not necessary.
    # But is nice to have for recursively finding all the possibles hop combinations.
    id = Column(Integer, default=0)
    pair_id = Column(String, primary_key=True)
    offer_denom = Column(String, ForeignKey(
        "whitelisted_token.denom", ondelete="CASCADE"))
    ask_denom = Column(String, ForeignKey(
        "whitelisted_token.denom", ondelete="CASCADE"))

    # __table_args__ = (UniqueConstraint('id'), )

    def __init__(self, astro_swap: AstroSwap):
        self.pair_id = WhitelistedHop.build_pair_id(astro_swap)
        self.offer_denom = astro_swap.offer_asset_info.denom
        self.ask_denom = astro_swap.ask_asset_info.denom

    @staticmethod
    def build_pair_id(astro_swap: AstroSwap):
        l = [astro_swap.offer_asset_info.denom,
             astro_swap.ask_asset_info.denom]
        # By sorting l we ensure that the pair_id field is unique. This means that
        # AstroSwap(A,B) or AstroSwap(B,A) define the same hop.
        l.sort()
        return "-".join(l)

    def __repr__(self) -> str:
        repr = ["{}={}".format(k, self.__dict__[k])
                for k in self.__dict__.keys() if k != "_sa_instance_state"]
        nice_string = """
    """.join(repr)
        return """[
    {}
]""".format(nice_string)


# We use a trigget to autoincrement column id becaucse the autoincrement feature does not
# work on non primary key column.
increment_id = DDL("""
CREATE TRIGGER increment_id AFTER INSERT ON whitelisted_hop
BEGIN
      UPDATE whitelisted_hop 
        SET id = (SELECT MAX(Id) FROM whitelisted_hop) + 1
      WHERE  pair_id = new.pair_id  ; 
END
  """)
event.listen(WhitelistedHop.__table__, 'after_create', increment_id)
