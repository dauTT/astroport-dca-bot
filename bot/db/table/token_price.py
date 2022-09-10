from typing import Optional
from sqlalchemy import Column, String, Integer, \
    Float, DateTime, DDL, event
from bot.db.base import Base
from bot.db.table import row_string
from datetime import datetime


class TokenPrice(Base):
    __tablename__ = 'token_price'

    denom = Column(String, primary_key=True)
    coingecko_id = Column(String, nullable=False)
    coingecko_symbol = Column(String)
    price = Column(Float)
    conversion = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow())

    def __init__(self, denom: str, coingecko_id: str,
                 coingecko_symbol: str,  conversion: int, price: Optional[float] = None):
        self.denom = denom
        self.coingecko_id = coingecko_id
        self.coingecko_symbol = coingecko_symbol
        self.conversion = conversion
        self.price = price

    def __repr__(self) -> str:
        return row_string(self)


trigger_updated_at = DDL("""
CREATE TRIGGER trigger_updated_at AFTER UPDATE ON token_price
BEGIN
      UPDATE token_price
        SET updated_at = datetime('now') 
            
      WHERE  
        denom = new.denom;
END
  """)
event.listen(TokenPrice.__table__, 'after_create', trigger_updated_at)
