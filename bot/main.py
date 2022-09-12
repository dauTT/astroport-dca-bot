import os
import logging
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.blocking import BlockingScheduler
from bot.exec_order import ExecOrder
from bot.db_sync import initialize_db
from bot.settings import LOG_PATH_FILE, SYNC_USER_FREQ, SYNC_CFG_FREQ, \
    SCHEDULE_ORDER_FREQ, SYNC_TOKEN_PRICE_FREQ
from pathlib import Path


def init_log(logging_level):
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging_level)
    formatter = logging.Formatter(format)

    # create a folder if it does not exist
    FOLDER_PATH = os.path.dirname(LOG_PATH_FILE)
    Path(FOLDER_PATH).mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(LOG_PATH_FILE,
                                       maxBytes=1024 * 1024 * 10,
                                       backupCount=4)
    file_handler.setLevel(logging_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = init_log(logging.INFO)


def clean_db():
    from bot.db.database import drop_database_objects
    drop_database_objects()


def start():
    """
        When the bot start it will reschedule all the orders in the DB, regardless
        of whether they have been already schedule in the past or not.
    """
    DCA_BOT = os.environ['DCA_BOT']
    assert DCA_BOT in [
        'dev', 'prod', 'test'], "Please configure the environment variable DCA_BOT "

    logger.info(
        "*************** ENVIRONMENT: {} **********************".format(os.environ['DCA_BOT']))
    logger.info("*************** BOT START ****************************")
    bot = ExecOrder()

    scheduler = BlockingScheduler(timezone='utc')
    oders = bot.db.get_dca_orders()
    bot.schedule_next_run(oders, scheduler)

    # schedule recurrening job
    scheduler.add_job(bot.sync_users_data, 'interval', id="sync_users_data",
                      minutes=SYNC_USER_FREQ)
    scheduler.add_job(bot.sync_dca_cfg, 'interval', id="sync_dca_cfg",
                      minutes=SYNC_CFG_FREQ)
    scheduler.add_job(bot.schedule_orders, 'interval',
                      minutes=SCHEDULE_ORDER_FREQ, id="schedule_orders",  args=[scheduler])
    scheduler.add_job(bot.sync_token_price, 'interval',
                      minutes=SYNC_TOKEN_PRICE_FREQ, id="sync_token_price")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.DEBUG)
    # logging.getLogger('bot.db.database').setLevel(logging.DEBUG)
    # logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    # clean_db()

    # load initial dca users into the database and
    # fill price table
    initialize_db()

    # Once the bot start to process the initial user orders, we can still include new users
    # by adding them to the database directly via sql or in this way:
    # """
    # s = Sync()
    # s.insert_user_into_db(new_user_address)
    # """"
    start()
