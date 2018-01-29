from strategy import Signal, format_pnl
from market_data.assets import get_ohlc_since_as_df
from time import sleep, time
from datetime import datetime
import logger
from logging import INFO, WARNING, ERROR, DEBUG


LOG = logger.getLogger(__name__)

MAX_TRADE_ATTEMPT_NB = 5


class TradingSystem:
    def __init__(self, strategy, cash, pair, trades=None, simul=True):
        self._cash = cash
        self._pair = pair
        self._simul = simul
        # log(INFO,'initializing prices from histo for %s' % pair)
        # prices = load_ohlc_histo(pair)
        self._strategy = strategy
        print(self._strategy)

    def __str__(self):
        return 'pair=%s, simul=%s, ' % (self._pair, self._simul) + str(self._strategy)

    def format_msg(self, msg, signal=None):
        text = ''
        if self._pair:
            text += '[%s]' % self._pair
        if self._strategy.get_shortname():
            text += '[%s]' % self._strategy.get_shortname()
        text += ' %s' % msg
        if signal:
            text += ' - %s' % signal
        return text

    def log(self, msg, level=INFO, signal=None, send=False):
        msg = self.format_msg(msg, signal)
        if level == INFO:
            LOG.info(msg, send=send)
        if level == ERROR:
            LOG.error(msg, send=send)
        if level == WARNING:
            LOG.warning(msg, send=send)
        if level == DEBUG:
            LOG.debug(msg, send=send)

    def process_signal(self, signal, trade_price):
        if signal == Signal.PASS:
            return
        attempts = 0
        self.log('%s triggered! Trying to execute the trade ...' % signal
                 ,signal=signal, send=True)
        price, err = sell(trade_price, self._simul)
        while err is not None and attempts < MAX_TRADE_ATTEMPT_NB:
            self.log('No trade confirmation received. Re-attempting(%d) to place trade.\n'
                     'Error is : %s' % (attempts, err), level=ERROR)
            attempts += 1
            if signal == Signal.BUY:
                price, err = buy(trade_price, self._simul)
            if signal in [Signal.SELL, Signal.LOCAL_STOP_LOSS, Signal.STOP_LOSS]:
                price, err = sell(trade_price, self._simul)
        if attempts == MAX_TRADE_ATTEMPT_NB and err is not None:
            self.log('Aborting trade after no confirmation was received.', level=ERROR,
                     send=True,
                     signal=signal)
        else:
            trade_time = int(time())
            self._strategy.update_trades(signal, price, trade_time)
            self.log('Trade executed @%f at %s' % (price, datetime.fromtimestamp(trade_time))
                     , level=ERROR, signal=signal, send=True)
            logger.save_trades(self._strategy.get_trades(), self._pair)

        pnl = self._strategy.calc_pnl()
        self.log(format_pnl(pnl), send=True)

    def start(self):
        sleep_time = self._strategy.get_step()/3
        start = time()
        since = start-2*self._strategy.get_step()
        self.log('====Trading System TradingSystem1 started===== %s' % self.__str__(), send=True)
        signal_frequency = self._strategy.get_step()/sleep_time
        counter = 0
        while True:
            self.log('Pulling prices since %s' % datetime.fromtimestamp(since))
            prices = get_ohlc_since_as_df(self._pair, since, 0)
            if prices is None:
                self.log('Unable to pull prices. Retrying at %s' % (datetime.fromtimestamp(time() + sleep_time))
                         , level=ERROR)
                sleep(sleep_time)
                continue
            counter += 1
            since = prices.TIMESTAMP.iloc[-1]

            self._strategy.refresh_prices(prices)

            self.log('Calculating signal')
            signal, trade_price = self._strategy.get_signal(prices, refresh=False)
            self.log('Signal received : %s' % signal)
            if signal == Signal.STOP_LOSS:
                self.process_signal(signal, trade_price)
                self.log('Shutting down', level=ERROR, signal=signal, send=True)
                return

            if signal == Signal.LOCAL_STOP_LOSS:
                self.process_signal(signal, trade_price)

            if counter % signal_frequency == 0:
                self.process_signal(signal, trade_price)

            self.log('Next signal at %s' % (datetime.fromtimestamp(time() + sleep_time)))
            sleep(sleep_time)


def buy(price, simul):
    return price, None


def sell(price, simul):
    return price, None
