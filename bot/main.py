import os
from time import sleep
from bot.exec_order import ExecOrder
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime, time

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta


from terra_sdk.client.localterra import LocalTerra
from bot.util import read_artifact
from bot.config import LOG_PATH_FILE


def init_log(logging_level):
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging_level)
    formatter = logging.Formatter(format)

    file_handler = RotatingFileHandler(LOG_PATH_FILE,
                                       maxBytes=1024 * 1024 * 50,
                                       backupCount=10)
    file_handler.setLevel(logging_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.INFO)
    logging.getLogger('bot.db.database').setLevel(logging_level)
    # logging.getLogger('apscheduler').setLevel(logging.INFO)

    return logger


if __name__ == "__main__":
    logger = init_log(logging.DEBUG)
    logger.info("*************** BOT START ****************************")

    network = read_artifact("localterra")
    terra = LocalTerra()
    exec = ExecOrder()

    oders = exec.db.get_dca_orders()

    # exec.db.exec_sql("DROP TABLE purchase_history")

    exec.purchase_and_sync(str(oders[0].id))

    exec.db.get_purchase_history()

    # if True:
    #     for order in oders:
    #         print(order)
    #         _day, _time = parse_time_seconds(
    #             order.last_purchase.real + order.interval.real)

    #         schedule_on(_day).at(_time).do(
    #             purchase_and_sync_once, order.id).tag(order.id)

    #         # schedule do(purchase_and_sync_once, order.id).tag(order.id)

    #         # schedule.every(order.interval.real).seconds.do(
    #         #    exec.purchase_and_sync, order.id).tag(order.id)
    #     i = 0
    #     while True:

    #         # Checks whether a scheduled task
    #         # is pending to run or not

    #         # if i == 0:
    #         #     schedule.run_all()
    #         #     i += 1
    #         all_jobs = schedule.get_jobs()
    #         print(all_jobs)
    #         schedule.run_pending()
    #         sleep(1)

    # scheduler = BlockingScheduler()

    # dd = datetime.now() + timedelta(seconds=3)
    # scheduler.add_job(tick, 'date', run_date=dd, args=['TICK'])

    # dd = datetime.now() + timedelta(seconds=6)
    # scheduler.add_job(tick, 'date', run_date=dd, kwargs={'text': 'TOCK'})

    # for order in oders:
    #     start_time = datetime.fromtimestamp(
    #         order.interval.real + order.last_purchase.real + 1400)

    #     scheduler.add_job(exec.purchase_and_sync, 'date',
    #                       run_date=start_time,  id=order.id,  args=[order.id])

    # try:

    #     print(scheduler.get_jobs())

    #     scheduler.start()

    #     print(scheduler.get_jobs())

    # except (KeyboardInterrupt, SystemExit):
    #     # Not strictly necessary if daemonic mode is enabled but should be done if possible
    #     scheduler.shutdown()
