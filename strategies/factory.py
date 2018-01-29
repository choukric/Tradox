from heikin import StrategyHEIKINClassic


def create_strategy(name):
    if name is None or type(name) is not str:
        return None
    params = name.split('_')
    if len(params) < 2:
        return None
    if params[0] == 'H' or params[0] == 'h':
        candles = None
        bodies = None
        local_stop_loss = None
        stop_loss = None
        step = get_int(params[1],None)
        if len(params) > 2:
            candles = get_int(params[2],None)
        if len(params) > 3:
            bodies = get_int(params[3], None)
        if len(params) > 4:
            local_stop_loss = get_float(params[4], None, 0.01)
        if len(params) > 5:
            stop_loss = get_float(params[5], None, 0.01)
        if step is None or candles is None or bodies is None:
            return None
        return StrategyHEIKINClassic(prices=None,
                                     step=step,
                                     nb_of_candles=candles,
                                     nb_of_bodies=bodies,
                                     local_stop_loss=local_stop_loss,
                                     stop_loss=stop_loss)


def get_int(s, default):
    try:
        return int(s)
    except ValueError:
        return default


def get_float(s, default, factor=1):
    try:
        return float(s)*factor
    except ValueError:
        return default
