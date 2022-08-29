from sqlalchemy import Column, String, Integer, Date
from bot.db.base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(String, primary_key=True)

    def __init__(self, user_address: str):
        self.id = user_address

    def __repr__(self) -> str:
        return "id={}".format(self.id)
