import sys
sys.path.append('../src')

import pybit

if __name__ == "__main__":
    conn = pybit.local_rpc_channel()  # will use read_default_config
    assert(conn.getinfo().testnet) # don't test on prodnet

    tx = pybit.send_from_address(
        from_address='mmxX1HBtcFXXvtRpZHxzkztrnL4EKs7SbJ',
        payments={
            'n1K4inDt3gYUsmtxavty2Jc8M2Jt2U6meg':1,
            'myH4W26fRNcwSPrUeWbPh9VQWjAfDk8Bwz':2,
        },
        change_address='mmxX1HBtcFXXvtRpZHxzkztrnL4EKs7SbJ'
    )
    print 'payment transaction hash:', tx