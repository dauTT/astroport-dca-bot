import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
from bot.exec_order import ExecOrder
from bot.config import LOG_PATH_FILE


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
    oders = exec.db.get_dca_orders()
    # exec.db.exec_sql("DROP TABLE dca_order")
    # exec.purchase_and_sync("terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v-1")
    # exec.purchase_and_sync(str(oders[1].id))
    # exec.purchase_and_sync(str(oders[2].id))
    # exec.purchase_and_sync(str(oders[3].id))

    if True:
        scheduler = BlockingScheduler()

        delta = 20
        for order in oders:

            next_run_time = datetime.fromtimestamp(
                order.interval.real + order.last_purchase.real)

            if next_run_time < datetime.now():
                next_run_time = datetime.now() + timedelta(seconds=delta)
                delta += 60

            scheduler.add_job(exec.purchase_and_sync, 'date',
                              run_date=next_run_time,  id=order.id,  args=[order.id, scheduler])

            # for job in scheduler.get_jobs():
            #     logger.debug(job.__slots__)
            #     logger.debug(job.id, job.trigger, job.name)

            logger.debug(
                "update order_id={}: schedule=True, next_run_time={}".format(
                    order.id, next_run_time))
            order.schedule = True
            order.next_run_time = next_run_time
            exec.db.insert_or_update(order)

        try:
            scheduler.start()

        except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            scheduler.shutdown()


if __name__ == "__main__":
    logger = init_log(logging.INFO)
    # logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.INFO)
    # logging.getLogger('bot.db.database').setLevel(logging.INFO)
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    start()
