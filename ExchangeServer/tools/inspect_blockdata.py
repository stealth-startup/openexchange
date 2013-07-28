__author__ = 'Rex'


# usage:
#   python inspect_blockdata [height]

import sys
sys.path.append('..')

import data_management as dm


if __name__ == "__main__":
    try:
        height = int(sys.argv[1])
        exchange = dm.load_data(str(height),dm.BLOCKS_FOLDER)
    except:
        exchange = dm.pop_exchange()

    print exchange.exchange


