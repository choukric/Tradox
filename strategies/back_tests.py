from market_data import histo, assets
import strategy
from heikin import StrategyHEIKINClassic
import pandas as pd
import numpy as np
from collections import namedtuple

BackTestResult = namedtuple('BackTestResult', 'Pair, Step, BackTest, Candles, UseBody, LocalStopLoss')


def backtest_heikin():
    pairs = assets.get_all_assets_for_quote('ZEUR')
    result = {'CCY': [],
              'STEP': [],
              'CANDLES': [],
              'BODY': [],
              'PNL': []}
    for pair in pairs:
        best_step = 0
        best_back_test = strategy.PNL(-99999,0,0,False)
        best_nb_of_candles = 0
        best_nb_of_bodies = 0
        best_local_stop_loss = 0
        prices = histo.load_ohlc_histo(pair)
        # steps = 3600 * np.array([0.1, 0.5, 1, 2, 12])
        steps = 3600 * np.array([0.5])
        # nb_of_candles_list = [2, 3, 4, 5]
        nb_of_candles_list = [3,4]
        nb_of_bodies_list = [2,3]
        local_stop_loss_list = [0, 0.95, 0.9, 0.8]
        for step in steps:
            for nb_of_candles in nb_of_candles_list:
                for nb_of_bodies in nb_of_bodies_list:
                    for local_stop_loss in local_stop_loss_list:
                        s = StrategyHEIKINClassic(prices=prices,
                                                  step=step,
                                                  nb_of_candles=nb_of_candles,
                                                  nb_of_bodies=nb_of_bodies,
                                                  stop_loss=0.6,
                                                  local_stop_loss=local_stop_loss)
                        back_test = s.backtest()
                        if back_test.Perf > best_back_test.Perf:
                            best_back_test = back_test
                            best_step = step
                            best_nb_of_candles = nb_of_candles
                            best_nb_of_bodies = nb_of_bodies
                            best_local_stop_loss = local_stop_loss
                        # df = s.get_heikin_prices()
                        # df.to_csv('backtests/HEIKIN1/%s_candles_%d_%s_%s.csv' % (pair, step,nb_of_bodies,nb_of_candles))
                        # df = s.get_trades()
                        # df.to_csv('backtests/HEIKIN1/%s_trades_%d_%s_%s.csv' % (pair, step,nb_of_bodies,nb_of_candles))
                        # result['CCY'].append(pair)
                        # result['STEP'].append(step)
                        # result['CANDLES'].append(nb_of_candles)
                        # result['BODY'].append(nb_of_bodies)
                        # result['PNL'].append(back_test.PNL)

        best = BackTestResult(Step=best_step,
                              Pair=pair,
                              Candles=best_nb_of_candles,
                              LocalStopLoss=best_local_stop_loss,
                              BackTest=best_back_test,
                              UseBody=best_nb_of_bodies)
        print(best)
    # df = pd.DataFrame(result)
    # df.to_csv('backtests/HEIKIN1/Summary.csv')

if __name__ == "__main__":
    backtest_heikin()



