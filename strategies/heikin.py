from strategy import Strategy, Signal
from collections import deque
import pandas as pd
import numpy as np


class StrategyHEIKINClassic(Strategy):

    def __init__(self, prices, step=60, use_wick=True,
                 nb_of_candles=2, nb_of_bodies=2, trades=None, stop_loss=None, local_stop_loss=None):
        Strategy.__init__(self, prices, trades=trades, step=step, stop_loss=stop_loss, local_stop_loss=local_stop_loss)
        self._use_wick = use_wick
        self._nb_of_candles = nb_of_candles
        self._nb_of_bodies = nb_of_bodies
        self._heikin_prices = pd.DataFrame({'OPEN': [],
                                           'HIGH': [],
                                           'LOW': [],
                                           'CLOSE': [],
                                           'COLOR': [],
                                           'PRICE': [],
                                           'TIMESTAMP': []})
        self.refresh_heikin_prices()

    def __str__(self):
        return super(StrategyHEIKINClassic, self).__str__() + ', wick=%s, candles=%i, bodies=%i' \
                                                              '' %(self._use_wick,self._nb_of_candles,self._nb_of_bodies)

    def get_shortname(self):
        name = 'H_%i_%i_%i' % (self._step, self._nb_of_candles, self._nb_of_bodies)
        if self._local_stop_loss:
            name += '_%i' % int(100 * self._local_stop_loss)
        if self._stop_loss:
            name += '_%i' % int(100 * self._stop_loss)
        return name

    @staticmethod
    def calc_heikin(o, h, l, c, oldO, oldC):
        ha_close = (o + h + l + c) / 4
        ha_open = (oldO + oldC) / 2
        elements = np.array([h, l, ha_open, ha_close])
        ha_high = elements.max(0)
        ha_low = elements.min(0)
        out = np.array([ha_open, ha_high, ha_low, ha_close])
        return out

    @staticmethod
    def is_bearish(heikin):
        return heikin[3] < heikin[0]

    @staticmethod
    def is_bullish(heikin):
        return heikin[3] > heikin[0]

    @staticmethod
    def get_body(heikin):
        return np.absolute(heikin[3] - heikin[0])

    @staticmethod
    def has_upper_wick(heikin):
        return heikin[0] != heikin[1]

    @staticmethod
    def has_lower_wick(heikin):
        return heikin[0] != heikin[2]

    @staticmethod
    def calc_heikin(o, h, l, c, oldO, oldC):
        ha_close = (o + h + l + c) / 4
        ha_open = (oldO + oldC) / 2
        elements = np.array([h, l, ha_open, ha_close])
        ha_high = elements.max(0)
        ha_low = elements.min(0)
        out = (ha_open, ha_high, ha_low, ha_close)
        return out

    def get_heikin_prices(self):
        return self._heikin_prices

    def refresh_heikin_prices(self):
        ha_close_list = self._heikin_prices.CLOSE
        ha_open_list = self._heikin_prices.OPEN
        ha_high_list = self._heikin_prices.HIGH
        ha_low_list = self._heikin_prices.LOW
        ha_color_list = self._heikin_prices.COLOR
        ha_close_list_temp = []
        ha_open_list_temp = []
        ha_high_list_temp = []
        ha_low_list_temp = []
        ha_color_list_temp = []
        oldO, oldC = (-1, -1)
        if len(self._heikin_prices)>0:
            oldO = self._heikin_prices.OPEN.iloc[-1]
            oldC = self._heikin_prices.CLOSE.iloc[-1]

        for i in xrange(len(self._heikin_prices), len(self._prices_step)):
            if oldO == -1:
                oldC = (self._prices_step.OPEN[i] +
                        self._prices_step.CLOSE[i] +
                        self._prices_step.HIGH[i] +
                        self._prices_step.LOW[i]) / 4
                oldO = (self._prices_step.CLOSE[i] + self._prices_step.OPEN[i]) / 2
            heikin = StrategyHEIKINClassic.calc_heikin(self._prices_step.OPEN[i],
                                                self._prices_step.HIGH[i],
                                                self._prices_step.LOW[i],
                                                self._prices_step.CLOSE[i],
                                                oldO, oldC)
            oldO, _, _, oldC = heikin
            ha_close_list_temp.append(heikin[3])
            ha_open_list_temp.append(heikin[0])
            ha_high_list_temp.append(heikin[1])
            ha_low_list_temp.append(heikin[2])
            ha_color_list_temp.append(np.where(StrategyHEIKINClassic.is_bearish(heikin), 'RED',
                                          np.where(StrategyHEIKINClassic.is_bullish(heikin), 'GREEN', 'WHITE')))
        ha_close_list = pd.concat([ha_close_list, pd.Series(ha_close_list_temp)], ignore_index=True)
        ha_open_list = pd.concat([ha_open_list, pd.Series(ha_open_list_temp)], ignore_index=True)
        ha_high_list = pd.concat([ha_high_list, pd.Series(ha_high_list_temp)], ignore_index=True)
        ha_low_list = pd.concat([ha_low_list, pd.Series(ha_low_list_temp)], ignore_index=True)
        ha_color_list = pd.concat([ha_color_list, pd.Series(ha_color_list_temp)], ignore_index=True)

        self._heikin_prices = pd.DataFrame({'OPEN': ha_open_list,
                                            'HIGH': ha_high_list,
                                            'LOW': ha_low_list,
                                            'CLOSE': ha_close_list,
                                            'COLOR': ha_color_list,
                                            'PRICE': [] if not len(self._prices_step) else self._prices_step.CLOSE,
                                            'TIMESTAMP': [] if not len(self._prices_step) else self._prices_step.TIMESTAMP})
        Strategy.add_dates_to_df(self._heikin_prices)

    def refresh_prices(self, prices=None):
        if prices is None:
            return
        super(StrategyHEIKINClassic, self).refresh_prices(prices)
        self.refresh_heikin_prices()

    def get_signal_from_heikin(self,heikin_prevs,price):
        is_open_deal = len(self._trades) > 0 and self._trades.SIGN.iloc[-1] == Signal.BUY

        if self.stop_loss(price):
            return Signal.STOP_LOSS

        if self.local_stop_loss(price):
            return Signal.LOCAL_STOP_LOSS

        if len(heikin_prevs) < self._nb_of_candles:
            return Signal.PASS

        body_increasing = False
        bearish = True
        for h in heikin_prevs:
            if not StrategyHEIKINClassic.is_bearish(h):
                bearish = False
                break
        bullish = True
        for h in heikin_prevs:
            bullish = bullish and StrategyHEIKINClassic.is_bullish(h)
            if not bullish:
                break
        if self._nb_of_bodies <= self._nb_of_candles and self._nb_of_bodies != 0:
            body_increasing = all(StrategyHEIKINClassic.get_body(heikin_prevs[i]) <= StrategyHEIKINClassic.get_body(
                heikin_prevs[i + 1])
                                  for i in xrange(len(heikin_prevs) - self._nb_of_bodies, len(heikin_prevs) - 1))
        no_wick = not StrategyHEIKINClassic.has_upper_wick(heikin_prevs[-1]) if self._use_wick else True
        if (not is_open_deal) and bearish and body_increasing and no_wick:
            # go long
            return Signal.BUY

        no_wick = not StrategyHEIKINClassic.has_lower_wick(heikin_prevs[-1]) if self._use_wick else True
        if is_open_deal and bullish and no_wick and body_increasing:
            # go short
            return Signal.SELL

        return Signal.PASS

    def get_signal(self, prices=None, refresh=False):
        if prices is None:
            return Signal.PASS
        if refresh:
            self.refresh_prices(prices)
        heikin_prevs = deque(maxlen=self._nb_of_candles)
        for i in self._heikin_prices.index[-3::]:
            ha_close = self._heikin_prices.CLOSE[i]
            ha_open = self._heikin_prices.OPEN[i]
            ha_high = self._heikin_prices.HIGH[i]
            ha_low = self._heikin_prices.LOW[i]
            heikin = (ha_open, ha_high, ha_low, ha_close)
            heikin_prevs.append(heikin)
        return self.get_signal_from_heikin(heikin_prevs,
                                           self._prices_step.CLOSE.iloc[-1]), self._prices_step.CLOSE.iloc[-1]


    def calc_trades(self):
        heikin_prevs = deque(maxlen=self._nb_of_candles)
        for i in self._prices_step.index:
            ha_close = self._heikin_prices.CLOSE[i]
            ha_open = self._heikin_prices.OPEN[i]
            ha_high = self._heikin_prices.HIGH[i]
            ha_low = self._heikin_prices.LOW[i]
            heikin = (ha_open, ha_high, ha_low, ha_close)
            heikin_prevs.append(heikin)
            sig = self.get_signal_from_heikin(heikin_prevs,
                                              self._prices_step.CLOSE[i])

            if sig == Signal.PASS:
                continue

            self.update_trades(signal=sig,
                               price=self._prices_step.CLOSE.iloc[i],
                               timestamp=self._prices_step.TIMESTAMP.iloc[i])

            if sig == Signal.STOP_LOSS:
                return
