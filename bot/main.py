import os
from bot.exec_order import ExecOrder
import logging
from logging.handlers import RotatingFileHandler
import sys

LOG_PATH_FILE = "./logs/bot.log"


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

    logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.INFO)
    logging.getLogger('bot.db.database').setLevel(logging_level)
    return logger


if __name__ == "__main__":
    logger = init_log(logging.DEBUG)
    logger.info("*************** BOT START ****************************")

    # exec = ExecOrder()
    # exec.db.get_dca_orders()

    pass
