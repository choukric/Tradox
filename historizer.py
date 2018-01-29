import logger
log = logger.getLogger('Historizer')

from market_data import histo
import sys, getopt


def main(argv):
    histo_dir = ''
    quote_ccy = 'ZEUR'

    try:
        opts, args = getopt.getopt(argv, "z:q:")
    except getopt.GetoptError:
        print('historizer.py -z <histo directory> -q <quote currency>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('historizer.py -z <histo directory> -q <quote currency>')
            sys.exit()
        elif opt in ("-z"):
            histo_dir = arg
        elif opt in ("-q"):
            quote_ccy = arg

    log.info('Starting historization')
    log.info('settings : histo_dir=%s, quote_ccy=%s' %  (histo_dir, quote_ccy))
    histo.init(histo_dir)
    histo.import_then_save_all_pairs_for_quote(quote_ccy)
    log.info('End historization')


if __name__ == "__main__":
    main(sys.argv[1:])
