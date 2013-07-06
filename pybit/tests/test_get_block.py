import sys
sys.path.append('../src')

import pybit

if __name__ == "__main__":
    conn = pybit.local_rpc_channel()  # will use read_default_config
#    assert conn.getinfo().testnet  # don't test on prodnet

    print pybit.get_block_by_height(80801)
