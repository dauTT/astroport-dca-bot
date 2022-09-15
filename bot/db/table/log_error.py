from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from bot.db.base import Base
from bot.db.table import row_string
from datetime import datetime
from typing import Optional


class LogError(Base):
    __tablename__ = 'log_error'

    id = Column(Integer, primary_key=True)
    create_at = Column(DateTime, default=datetime.utcnow())
    order_id = Column(String, ForeignKey("dca_order.id", ondelete="CASCADE"))
    user_address = Column(String, ForeignKey("user.id", ondelete="CASCADE"))
    calling_method = Column(String)
    msg = Column(String)

    def __init__(self,  order_id: Optional[str], user_address: Optional[str], calling_method: str,  msg: str):
        self.order_id = order_id
        self.user_address = user_address
        self.calling_method = calling_method
        self.msg = msg

    def __repr__(self) -> str:
        return row_string(self)
