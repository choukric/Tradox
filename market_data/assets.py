from request_interface import get_public_result_for_pair, public_request
from custom_exceptions import KrakenPublicException
import pandas as pd
from datetime import datetime
import logger

LOG = logger.getLogger(__name__)

ATTEMPTS_MAX = 5
QUOTE = 'quote'
BASE = 'base'


def get_asset_pairs():
    return public_request('AssetPairs')


def get_ohlc(pair, l=None):
    try:
        return get_public_result_for_pair('OHLC', l=l, pair=pair)
    except KrakenPublicException as e:
        raise KrakenPublicException(e.message)


def get_ticker_info(pair):
    return get_public_result_for_pair('Ticker', pair)
    

def get_ask(ticker):
    try:
        return ticker['a']
    except KeyError:
        return None
    

def get_bid(ticker):
    try:
        return ticker['b']
    except KeyError:
        return None


def get_last(ticker):
    try:
        return ticker['c'][0]
    except KeyError:
        return None


def get_low(ticker):
    try:
        return ticker['l']
    except KeyError:
        return None


def get_high(ticker):
    try:
        return ticker['h']
    except KeyError:
        return None


def get_open(ticker):
    try:
        return ticker['o']
    except KeyError:
        return None


def get_order_book(pair):
    return get_public_result_for_pair('Depth', pair)


def get_ohlc_since(pair, since, attempts=0):
    try:
        return get_public_result_for_pair('OHLC', pair, since=since)
    except KrakenPublicException as error:
        LOG.error(error)
        if attempts == ATTEMPTS_MAX:
            LOG.error('Reached the max nb of attempts requesting get_ohlc_since %s! Aborting!' % pair)
            return None
        attempts += 1
        LOG.error('Problem while requesting data for %s. Re-attempting (nb %d)' % (pair, attempts))
        return get_ohlc_since(pair, since, attempts)
    except ValueError as error:
        LOG.error(error)
        if attempts == ATTEMPTS_MAX:
            LOG.error('Reached the max nb of attempts requesting get_ohlc_since %s! Aborting!' % pair)
            return None
        attempts += 1
        LOG.error('Problem while requesting data for %s. Re-attempting (nb %d)' % (pair, attempts))
        return get_ohlc_since(pair, since, attempts)


def get_ohlc_since_as_df(pair, since, attempts=0):
    data = get_ohlc_since(pair, since, attempts)
    if data is None:
        return None
    else:
        return ohlc_to_df(data,pair)


def get_open_prices(ohlc):
    if ohlc is None or ohlc == {}:
        return None
    d = {float(e[0]): float(e[1])
            for e in ohlc[ohlc.keys()[0]]}
    return {k:d[k] for k in sorted(d.iterkeys())}


def get_close_prices(ohlc):
    if ohlc is None:
        return None
    d = {float(e[0]): float(e[1])
            for e in ohlc[ohlc.keys()[0]]}
    return {k:d[k] for k in sorted(d.iterkeys())}


def get_high_prices(ohlc):
    if ohlc is None:
        return None
    d = {float(e[0]): float(e[1])
            for e in ohlc[ohlc.keys()[0]]}
    return {k: d[k] for k in sorted(d.iterkeys())}


def get_low_prices(ohlc):
    if ohlc is None:
        return None
    d = {float(e[0]): float(e[1])
            for e in ohlc[ohlc.keys()[0]]}
    return {k:d[k] for k in sorted(d.iterkeys())}


def ohlc_to_df(ohlc, pair):
    if ohlc is None:
        LOG.error('ohlc` is none')
        return
    if len(ohlc) == 0:
        return pd.DataFrame(columns=['TIMESTAMP','OPEN','HIGH','LOW','CLOSE','VWAP','VOLUME','COUNT'])
    data = ohlc[pair]
    df = pd.DataFrame(data=data,columns=['TIMESTAMP','OPEN','HIGH','LOW','CLOSE','VWAP','VOLUME','COUNT'])
    df.OPEN = pd.to_numeric(df.OPEN)
    df.HIGH = pd.to_numeric(df.HIGH)
    df.LOW = pd.to_numeric(df.LOW)
    df.CLOSE = pd.to_numeric(df.CLOSE)
    df['DATE'] = df.TIMESTAMP.apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
    return df


def get_all_assets(attempts=0):
    try:
        return get_asset_pairs()
    except KrakenPublicException as error:
        LOG.error(error)
        if attempts == ATTEMPTS_MAX:
            LOG.error('Reached the max nb of attempts requesting get_all_assets! Aborting!')
            return
        attempts += 1
        LOG.error('Problem while requesting data. Re-attempting (nb %d)' % attempts)
        return get_all_assets(attempts)
    except ValueError as error:
        LOG.error(error)
        if attempts == ATTEMPTS_MAX:
            LOG.error('Reached the max nb of attempts requesting get_all_assets! Aborting!')
            return
        attempts += 1
        LOG.error('Problem while requesting data. Re-attempting (nb %d)' % attempts)
        return get_all_assets(attempts)


def get_all_assets_for_quote(ccy):
    res = {}
    pairs = get_all_assets()
    for item in pairs.items():
        if not item[1]['quote'] == ccy or item[0].__contains__('.'):
            continue
        res[item[0]] = item[1]
    return res


def get_quote_currency(asset):
    if asset is None:
        return None
    return asset[QUOTE]


def get_base_currency(asset):
    if asset is None:
        return None
    return asset[BASE]


def get_assets_with_multiple_quotes(pairs,exclude=None):
    res = {}
    for name, value in pairs.items():
        quote = get_quote_currency(value)
        if exclude is not None and quote in exclude:
            continue
        base = get_base_currency(value)
        if base in res:
            res[base].append(quote)
        else:
            res[base] = [quote]
    for base,quotes in res.items():
        if len(quotes) < 2:
            del res[base]
    return res