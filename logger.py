import logging
import time
from mail.mail import report_email
from os import path

DEFAULT_LOG_DIR = '/Users/Chafik/workspace/python/my_projects/crypto_currency/tradox/logs'
LOGGER = None
LOG_ID = ''


class LoggerWithEmail(object):
    def __init__(self, logger):
        self.__logger = logger

    @report_email
    def info(self, msg, send=False):
        self.__logger.info(msg)

    @report_email
    def error(self, msg, send=False):
        self.__logger.error(msg)

    @report_email
    def debug(self, msg, send=False):
        self.__logger.debug(msg)

    @report_email
    def warning(self, msg, send=False):
        self.__logger.warning(msg)


def get_filename(name):
    global LOG_ID
    LOG_ID = '%s_%s' % (name, time.strftime("%Y%m%d_%H%M%S"))
    return DEFAULT_LOG_DIR + '/%s.log' % LOG_ID


def _init(name, filename):
    global LOGGER
    if not name:
        return LOGGER
    if not filename:
        filename = get_filename(name)
    logger = logging.getLogger(name)
    logger.addHandler(logging.StreamHandler())
    hdlr = logging.FileHandler(filename)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] - %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    formatter._fmt = '[' + name + ']' + formatter._fmt
    LOGGER = LoggerWithEmail(logger)


def getLogger(name=None,filename=None):
    if not LOGGER:
        _init(name, filename)
    return LOGGER


def save_trades(trades, pair):
    if trades is None or not len(trades):
        return
    report_name = DEFAULT_LOG_DIR + '/trades/%s_%s.csv' % (pair, LOG_ID)
    trades.to_csv(report_name)
