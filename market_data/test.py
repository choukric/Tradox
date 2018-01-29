import logger
log = logger.getLogger('test_histo')

import histo


pair = 'XETHZEUR'

histo.import_then_save_all_pairs_for_quote('ZEUR')
# histo.import_then_save_ohlc_for_pair(pair)