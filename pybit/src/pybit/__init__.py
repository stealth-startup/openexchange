def local_rpc_channel(filename=None):
    """
    Connect to default bitcoin instance owned by this user, on this machine.

    Returns a :class:`~bitcoinrpc.connection.BitcoinConnection` object.

    Arguments:

        - `filename`: Path to a configuration file in a non-standard location (optional)
    """
    from pybit.connection import BitcoinConnection
    from pybit.config import read_default_config

    cfg = read_default_config(filename)
    port = int(cfg.get('rpcport', '18332' if cfg.get('testnet') else '8332'))
    rcpuser = cfg.get('rpcuser', '')

    return BitcoinConnection(rcpuser, cfg['rpcpassword'], 'localhost', port)


def send_from_address(from_address, payments, change_address=None, wallet_pwd=None, minconf=1, maxconf=999999, min_fee=None, min_fee_per_tx=0):
    """
    note: the wallet will be locked after this op if it is encrypted
    return the transaction hash of the transaction
    payments are in BTC
    :type from_address: str
    :type payments: dict from str to float
    :type change_address: str or None
    :param change_address: if None, change_address will be a new generated address
    """
    from pybit.exceptions import NotEnoughFundError, ChangeAddressIllegitError, WalletWrongEncState, \
        SignRawTransactionFailedError

    rpc = local_rpc_channel()
    if from_address is None:
        unspents = rpc.listunspent(minconf, maxconf)
    else:
        unspents = [t for t in rpc.listunspent(minconf, maxconf) if t.address == from_address]

    send_sum = sum(payments.values())
    unspent_sum = sum([t.amount for t in unspents])
    min_fee = min_fee if min_fee is not None else rpc.getinfo().paytxfee

    if unspent_sum < send_sum + min_fee:
        raise NotEnoughFundError(unspents=unspents, unspent_sum=unspent_sum, send_sum=send_sum,min_fee=min_fee)

    #select unspents
    unspents.sort(key=lambda t:t.confirmations, reverse=True)

    chosen = []
    chosen_sum = 0
    fee = min_fee
    for t in unspents:
        chosen.append(t)
        chosen_sum += t.amount
        fee = max(min_fee, len(chosen)*min_fee_per_tx)
        if chosen_sum >= fee + send_sum:
            break

    change = float(chosen_sum - fee - send_sum)
    if change > 0:
        payments = dict(payments)  # make a copy of payments so that the original object won't be changed
        if change_address is None:
            change_address = rpc.getnewaddress()
        if change_address in payments:
            raise ChangeAddressIllegitError(change_address=change_address, payments=payments)
        payments[change_address] = change

    #compose raw transaction
    raw_tx = rpc.createrawtransaction(
        [{'txid':c.txid, 'vout':c.vout} for c in chosen],
        payments
    )

    #make sure the wallet is not locked
    if wallet_pwd:
        try:
            rpc.walletlock()  # lock the wallet so we make sure it has sufficient time in the later process
        except WalletWrongEncState:
            pass
        rpc.walletpassphrase(wallet_pwd, 10)  # unlock the wallet

    #sign raw transaction
    rst = rpc.signrawtransaction(raw_tx)
    if rst['complete'] == 0:
        raise SignRawTransactionFailedError(sign_result=rst)

    #lock the wallet
    if wallet_pwd:
        try:
            rpc.walletlock()
        except WalletWrongEncState:
            pass

    #send the signed raw transaction to the network
    return rpc.sendrawtransaction(rst['hex'])


def get_block_by_hash(block_hash):
    """
    return a block-chain style json-encoded block
    TODO: this is a very simple implementation and it do not analysis the signatures at all. it just ignored the
    non-standard transactions which should be considered.
    """
    def get_vout(raw_vout):
        value = int(raw_vout['value'] * 100000000)
        assert len(raw_vout['scriptPubKey']['addresses']) == 1
        address = raw_vout['scriptPubKey']['addresses'][0]
        return {
            'n': raw_vout['n'],
            'value': value,
            'addr': address,
        }

    def get_vin(rpc, raw_vin):
        tx_hash = raw_vin['txid']
        vout_n = raw_vin['vout']
        tx = rpc.decoderawtransaction(rpc.getrawtransaction(tx_hash, False))
        vout = [out for out in tx['vout'] if out["n"] == vout_n]
        assert len(vout) == 1

        return {
            'prev_out': get_vout(vout[0])
        }

    rpc = local_rpc_channel()
    raw_block = rpc.getblock(block_hash)
    block = {
        'height': raw_block['height'],
        'hash': raw_block['hash'],
        'prev_block': raw_block['previousblockhash'],
        'time': raw_block['time'],
        'bits': int(raw_block['bits'], 16),
        'main_chain': True,
        'tx':[],
    }

    for tx_hash in raw_block['tx']:
        try:
            raw_tx = rpc.decoderawtransaction(rpc.getrawtransaction(tx_hash, False))
            block['tx'].append({
                'hash': tx_hash,
                'inputs':[get_vin(rpc, d) for d in raw_tx['vin'] if 'coinbase' not in d],
                'out':[get_vout(d) for d in raw_tx['vout']],
            })
        except:
            pass  # none standards are just passed

    return {'blocks': [block] }


def get_block_by_height(height):
    """
    return a block-chain style json-encoded block
    """
    return get_block_by_hash(local_rpc_channel().getblockhash(height))
