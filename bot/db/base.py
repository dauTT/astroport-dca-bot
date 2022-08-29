from sqlalchemy import create_engine, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///bot/db/orders.db')
session_factory = sessionmaker(bind=engine)

Base = declarative_base()
