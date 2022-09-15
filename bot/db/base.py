from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from bot.settings import DB_URL


engine = create_engine(DB_URL, echo=False, connect_args={
                       'check_same_thread': False})
# To use foreign key constraint with sqlite, we need to enable this feature on the db level
event.listen(engine, 'connect', lambda c,
             _: c.execute('pragma foreign_keys=on'))

session_factory = sessionmaker(bind=engine)
Base = declarative_base()
