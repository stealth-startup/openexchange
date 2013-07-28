__author__ = 'Rex'


# usage:
#   python inspect_payment [height]

import sys
sys.path.append('..')

import data_management as dm


if __name__ == "__main__":
    try:
        height = int(sys.argv[1])
    except:
        height = None

    payments = dm.load_payments()
    if height is not None:
        print payments[height]
    else:
        print 'max processed height: %d' % max(payments.keys())
        print 'last payment'
        h = max(payments.keys())
        while h>0:
            try:
                record = payments[h]
                if record.transactions:
                    print 'height: %d' % h
                    print 'record: %s' % str(record)
                    break

                h-=1
            except:
                break

