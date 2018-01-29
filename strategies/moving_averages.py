from strategy import Strategy


class StrategyMA(Strategy):
    #step : in minutes
    def __init__(self, cash, prices, step = 60, slow = 10, fast = 5,threshold=0):
        Strategy.__init__(self, cash, prices, step)
        self._slow = slow
        self._fast = fast
        self._ma = {}
        self._threshold = threshold

    def calc_trades(self):
        ma = self._prices.copy()

        ma = ma.sort_values(by=['TIMESTAMP'])
        ma['SLOW'] = ma.PRICE.rolling(window=self._slow, center=False).mean().round(2)
        ma['FAST'] = ma.PRICE.rolling(window=self._fast, center=False).mean().round(2)
        ma['DIFF'] = ma.FAST - ma.SLOW
        ma['MOVE'] = (ma.FAST - ma.SLOW)/ma.SLOW
        ma['REGIME'] = np.where(ma.MOVE - self._threshold > 0, 1, 0)
        ma['REGIME'] = np.where(ma.MOVE + self._threshold < 0, -1, ma.REGIME)
        sign_list = []
        last_sign = 0
        last_r = 0
        for r in ma.REGIME:
            sign = np.sign(r-last_r)
            if sign == last_sign:
                sign = 0
            if r == 0:
                sign = 0
            if sign != 0:
                last_sign = sign
            sign_list.append(sign)
            last_r = r
        ma['SIGN'] = sign_list
        ma['ID'] = np.zeros(len(ma.index))
        ma.index = range(len(ma.index))
        idx = next(i for i in ma.index if ma.SIGN[i] == 1)
        ma = ma.drop(ma.index[[range(0, idx)]])
        ma.index = range(len(ma.index))

        last = 0
        for i in ma.index:
            if ma.SIGN[i] == 0:
                ma.at[i, 'ID'] = 0
            else:
                if ma.SIGN[i] == -1:
                    ma.at[i, 'ID'] = last
                else:
                    ma.at[i, 'ID'] = last + 1
                    last = last + 1

        trades = pd.concat([
            pd.DataFrame({'PRICE': ma.loc[ma.SIGN == 1, 'PRICE'],
                          'ID': ma.loc[ma.SIGN == 1, 'ID'],
                          'TIMESTAMP': ma.loc[ma.SIGN == 1, 'TIMESTAMP'],
                          'SIGN': 1}),
            pd.DataFrame({'PRICE': ma.loc[ma.SIGN == -1, 'PRICE'],
                          'ID': ma.loc[ma.SIGN == -1, 'ID'],
                          'TIMESTAMP': ma.loc[ma.SIGN == -1, 'TIMESTAMP'],
                          'SIGN': -1}),
        ])
        trades = trades.sort_values(by=['TIMESTAMP'])
        trades.index = range(len(trades.index))

        self._trades = trades
        self._ma = ma

        Strategy.add_dates_to_df(self._ma)
        Strategy.add_dates_to_df(self._trades)

    def plot_prices(self):
        to_plot = pd.DataFrame({'PRICE':self._ma.PRICE,
                                'SLOW':self._ma.SLOW,
                                'FAST':self._ma.FAST,
                                'DATE' : self._ma.DATE})
        to_plot.plot(x='DATE', y=['PRICE','SLOW','FAST'],grid=True)



