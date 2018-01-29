import abc
import pandas as pd
import numpy as np
from datetime import datetime
from collections import namedtuple
import logger
from enum import Enum

LOG = logger.getLogger(__name__)
PNL = namedtuple('PNL', 'Perf, HoldPerf, Gain, Estimated')


def format_pnl(pnl):
    perf, hold, gain, estimated = pnl
    return "Perf = %.2f%s, Hold = %.2f%s, Gain = %.2f%s, Estimated = %s" \
           % (perf, '%', hold, '%', gain, '%', estimated)

class Signal(Enum):
    BUY = 1
    SELL = -1
    STOP_LOSS = -2
    PASS = 0
    LOCAL_STOP_LOSS = -3


class Strategy(object):

    def __init__(self, prices, trades=None, step=60, stop_loss=None, local_stop_loss=None):
        self._step = step
        if prices is None:
            self._prices = pd.DataFrame({'TIMESTAMP': pd.Series(dtype=float),
                                         'PRICE': pd.Series(dtype=float)})
            self._prices_step = self._prices.copy()
        else:
            if len(prices) > 0 and step is not None:
                self._prices = Strategy.prices_change_step(prices, step)
                self._prices_step = Strategy.prices_change_step(prices, step)
            else:
                self._prices = prices
                self._prices_step = self._prices.copy()
        if trades is None:
            self._trades = pd.DataFrame({'TIMESTAMP': [],
                                         'ID' : [],
                                         'PRICE': [],
                                         'SIGN': []})
        else:
            self._trades = trades
        self._stop_loss = 0 if stop_loss is None else stop_loss
        self._local_stop_loss = 0 if local_stop_loss is None else local_stop_loss

    def __str__(self):
        return 'step=%d, local_stop_loss=%i' % (self._step, int(100*self._local_stop_loss)) + '%' + \
               ', stop_loss=%i' % int(100*self._stop_loss) + '%'

    def get_step(self):
        return self._step

    def stop_loss(self, price=None):
        if price is None:
            price = self._prices_step.CLOSE.iloc[-1]
        if not len(self._trades) or self._trades.SIGN.iloc[-1] != Signal.BUY:
            return 0
        return price < self._stop_loss*self._trades.PRICE.iloc[0]

    def local_stop_loss(self, price=None):
        if price is None:
            price = self._prices_step.CLOSE.iloc[-1]
        if not len(self._trades) or self._trades.SIGN.iloc[-1] != Signal.BUY:
            return 0
        return price < self._local_stop_loss * self._trades.PRICE.iloc[-1]


    @abc.abstractmethod
    def get_shortname(self):
        name = 'C_%i' % self._step
        if self._local_stop_loss:
            name += '_%i' % 100*self._local_stop_loss
        if self._stop_loss:
            name += '_%i' % 100*self._stop_loss
        return name

    @staticmethod
    def prices_change_step(prices, step):
        new_prices = prices.loc[(prices.TIMESTAMP - prices.iloc[-1].TIMESTAMP) % step == 0].copy()
        high = [prices[0:new_prices.index[0]].HIGH.max()]
        low = [prices[0:new_prices.index[0]].LOW.min()]
        for i in xrange(len(new_prices.index)-1):
            current_idx = new_prices.index[i]
            next_idx = new_prices.index[i+1]
            local_high = prices[current_idx:next_idx].HIGH.max()
            local_low = prices[current_idx:next_idx].LOW.min()
            high.append(local_high)
            low.append(local_low)
        new_prices['HIGH'] = high
        new_prices['LOW'] = low
        new_prices.index = range(len(new_prices))
        return new_prices

    @staticmethod
    def add_dates_to_df(df):
        df['DATE'] = df.TIMESTAMP.apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))


    @abc.abstractmethod
    def calc_trades(self):
        return

    @abc.abstractmethod
    def refresh_prices(self, prices=None):
        if prices is None:
            return
        self._prices = pd.concat([self._prices,prices])
        self._prices.drop_duplicates(['TIMESTAMP'], keep='last', inplace=True)
        self._prices.reset_index(drop=True)
        self._prices = self._prices.sort_values(by='TIMESTAMP')
        self._prices.index = range(len(self._prices.index))
        self._prices_step = self.prices_change_step(self._prices, self._step)

    @abc.abstractmethod
    def get_signal(self, prices=None):
        self.refresh_prices(prices)
        return Signal.Signal.PASS, 0

    def update_trades(self, signal, price, timestamp):
        trade_id = 0 if not len(self._trades) else self._trades.ID.iloc[-1]
        if signal == Signal.BUY:
            trade_id += 1
        id_series = self._trades.ID
        timestamp_series = self._trades.TIMESTAMP
        price_series = self._trades.PRICE
        sign_series = self._trades.SIGN

        self._trades.drop(labels=['ID', 'TIMESTAMP', 'PRICE', 'SIGN'], axis="columns", inplace=True)
        self._trades = pd.DataFrame({'TIMESTAMP': pd.concat([timestamp_series, pd.Series([timestamp])],
                                                            ignore_index=True),
                                     'ID' : pd.concat([id_series, pd.Series([trade_id])], ignore_index=True),
                                     'PRICE': pd.concat([price_series, pd.Series([price])], ignore_index=True),
                                     'SIGN': pd.concat([sign_series, pd.Series([signal])], ignore_index=True)})

        # LOG.info('Trade Update : trade sign %s @%f.' % (signal, price))

    def calc_pnl(self):
        cash = np.zeros(len(self._trades.index))
        last_cash = 1
        last_price = 1
        estimated = False
        for i in self._trades.index:
            if self._trades.SIGN.iloc[i] == Signal.BUY:
                cash[i] = - last_cash
            else:
                cash[i] = - last_cash * self._trades.PRICE.iloc[i] / last_price
            last_price = self._trades.PRICE.iloc[i]
            last_cash = cash[i]
        self._trades['CASH'] = cash
        total = self._trades.CASH.sum()
        if len(self._trades) and self._trades.SIGN.iloc[-1] == Signal.BUY:
            total += - last_cash * self._prices_step.CLOSE.iloc[-1] / last_price
            estimated = True
        perf = 100 * total
        hold_perf = 0
        if len(self._prices_step):
            hold_perf = 100 * (self._prices_step.CLOSE.iloc[-1] - self._prices_step.CLOSE.iloc[0]) / \
                    self._prices_step.CLOSE.iloc[0]
        return PNL(Perf=perf, HoldPerf=hold_perf, Gain=perf - hold_perf, Estimated=estimated)


    def backtest(self):
        self.calc_trades()
        return self.calc_pnl()

    def get_trades(self):
        Strategy.add_dates_to_df(self._trades)
        return self._trades
