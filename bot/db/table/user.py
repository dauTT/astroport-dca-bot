from sqlalchemy import Column, String, Boolean, DateTime
from bot.db.base import Base
from datetime import datetime
from bot.db.table import row_string


class User(Base):
    __tablename__ = 'user'

    # The id column is the user account address
    id = Column(String, primary_key=True)
    create_at = Column(DateTime, default=datetime.now())
    # sync_data column indicates if the process of syncing the user blockchain data
    # has already started or not. By dafault this flag is false for new user
    sync_data = Column(Boolean, default=False)

    def __init__(self, user_address: str, sync_data: bool = False):
        self.id = user_address
        self.sync_data = sync_data

    def set_sync_data(self, sync_data):
        self.sync_data = sync_data

    def __repr__(self) -> str:
        return row_string(self)
