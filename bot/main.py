import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
from bot.exec_order import ExecOrder
from bot.db_sync import Sync
from bot.config import LOG_PATH_FILE, SYNC_USER_FREQ, SYNC_CFG_FREQ, \
    SCHEDULE_ORDER_FREQ


def init_log(logging_level):
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging_level)
    formatter = logging.Formatter(format)

    file_handler = RotatingFileHandler(LOG_PATH_FILE,
                                       maxBytes=1024 * 1024 * 10,
                                       backupCount=4)
    file_handler.setLevel(logging_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = init_log(logging.INFO)


def start():
    """
        When the bot start it will reschedule all the orders in the DB, regardless
        of whether they have been already schedule in the past or not.
    """
    logger.info("*************** BOT START ****************************")
    exec = ExecOrder()
    # exec.db.exec_sql("DROP TABLE  user")
    # exec.purchase_and_sync("terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")

    scheduler = BlockingScheduler(timezone='utc')
    oders = exec.db.get_dca_orders()
    exec.schedule_next_run(oders, scheduler)

    # schedule recurrening job
    scheduler.add_job(exec.sync_users_data, 'interval', id="sync_users_data",
                      minutes=SYNC_USER_FREQ)
    scheduler.add_job(exec.sync_dca_cfg, 'interval', id="sync_dca_cfg",
                      minutes=SYNC_CFG_FREQ)
    scheduler.add_job(exec.schedule_orders, 'interval',
                      minutes=SCHEDULE_ORDER_FREQ, id="schedule_orders",  args=[scheduler])

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.INFO)
    # logging.getLogger('bot.db.database').setLevel(logging.INFO)
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    start()
