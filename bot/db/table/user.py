from sqlalchemy import Column, String
from bot.db.base import Base
from bot.db.table import row_string


class User(Base):
    __tablename__ = 'user'

    id = Column(String, primary_key=True)

    def __init__(self, user_address: str):
        self.id = user_address

    def __repr__(self) -> str:
        return row_string(self)
