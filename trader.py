import logger
LOG = logger.getLogger('Trader')

from strategies.ts import TradingSystem
from multiprocessing import Process
from strategies.factory import create_strategy
import sys


def startTS(c):
    c.start()


def main(strategy_code, pairs):
    strategy = create_strategy(strategy_code)
    trading_systems = [TradingSystem(strategy=strategy, cash=1000, pair=pair, simul=True) for pair in pairs]
    processes = [Process(target=startTS, args=[ts]) for ts in trading_systems]

    for p in processes:
        p.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        LOG.error('Not enough arguments! Usage : trader.py <strategy> <pair1> ... <pairN>')
    args = [arg.upper() for arg in args]
    try:
        LOG.info('=========== START =============')
        main(args[1], args[2:])
    except KeyboardInterrupt:
        LOG.error('Shutting down after signal from user!!!!\nBye!', send=True)
