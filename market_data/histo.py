from market_data import assets
from market_data.custom_exceptions import KrakenPublicException
import pandas as pd
from multiprocessing import Process, Lock
import logger

ATTEMPTS_MAX = 5
PATH = '/Users/Chafik/workspace/python/my_projects/crypto_currency/tradox/data/histo/'
LOG = logger.getLogger()


def init(path):
    global PATH
    PATH = path


def save_histo_ohlc_for_pair(pair, df):
    filename = PATH + 'ohlc/'+ pair + '_histo.csv'
    df2 = df
    try:
        csv_df = pd.read_csv(filename, index_col=0)
        df2 = pd.concat([csv_df, df])
        df2.drop_duplicates(['TIMESTAMP'], inplace=True)
        df2.reset_index(drop=True)
    except IOError as err:
        LOG.error('Problem with file for %s, Creating new one ...\n %s' % (pair, err))
    finally:
        df2 = df2.sort_values(by='TIMESTAMP')
        df2.index = range(len(df2.index))
        df2.to_csv(filename)


def import_then_save_ohlc_for_pair(pair,l=None,attempts=0):
    LOG.info('starting importing histo data for %s.' % pair)
    try:
        ohlc = assets.get_ohlc(l=l,pair=pair)
        df = assets.ohlc_to_df(ohlc,pair)
        save_histo_ohlc_for_pair(pair,df)
        LOG.info('ohlc histo file saved for %s.' % pair)
    except KrakenPublicException as error:
        LOG.error(error)
        if attempts == ATTEMPTS_MAX:
            LOG.error('Reached the max nb of attempts requesting import_then_save_ohlc_for_pair! Aborting!')
            return
        attempts += 1
        LOG.error('Problem while requesting data. Re-attempting (nb %d)' % attempts)
        import_then_save_ohlc_for_pair(pair, l=l, attempts=attempts)


def import_then_save_all_pairs_for_quote(quote):
    pairs = assets.get_all_assets_for_quote(quote)
    f = import_then_save_ohlc_for_pair
    lock = Lock()

    processes = [Process(target=f, args=(pair, lock)) for pair in pairs]
    for p in processes:
        p.start()

    for p in processes:
        p.join()


def load_ohlc_histo(pair):
    filename = PATH + 'ohlc/'+ pair + '_histo.csv'
    return pd.read_csv(filename, index_col=0)



