from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from bot.settings import DB_URL


engine = create_engine(DB_URL, echo=False, connect_args={
                       'check_same_thread': False})
session_factory = sessionmaker(bind=engine)
Base = declarative_base()
