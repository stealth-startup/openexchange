#use cron job to run the server script repeatedly
#cPickle benchmark:
#http://stackoverflow.com/questions/8514020/marshal-dumps-faster-cpickle-loads-faster
#so we should be OK with cPickle for a pretty long time

import openexchangelib
from openexchangelib import util
from openexchangelib.types import OEBaseException
import data_management as dm
from types import ExchangeServer
import json
import urllib2
import pybit


class CanNotFindPayOutTransactionError(OEBaseException):
    pass


def find_pay_out_transaction(height, log_address, exchange_address):
    """
    :type height: int
    :type log_address: str
    :type exchange_address: str
    """
    limit = 50  # start from 50
    while limit < 200000:
        data = json.load(
            urllib2.urlopen(url='http://blockchain.info/address/%s?format=json&limit=%d' % (log_address, limit), timeout=20))
        txs = {[od["value"] for od in d["out"] if od["addr"] == log_address][0]: d['hash'] for d in data['txs'] if
               d["inputs"][0]['prev_out']['addr'] == exchange_address}

        if height in txs:
            return txs[height]
        elif max(txs) < height:
            return None
        else:
            limit *= 2
    raise CanNotFindPayOutTransactionError()


def add_payment(all_payments, payments):
    """
    :type all_payments: dict from str to int
    :type payments: dict from str to int
    """
    for address, amount in payments.iteritems():
        assert amount >= 0
        if amount == 0:
            continue

        if address in all_payments:
            all_payments[address] += amount
        else:
            all_payments[address] = amount


def process_next_block():
    logger = util.get_logger('exchange_server')
    #1 if there's no market data, init one & save it & exit
    exchange = dm.load_exchange()
    if exchange is None:
        _exchange = openexchangelib.exchange0()
        exchange = ExchangeServer(_exchange, _exchange.processed_block_height, {})
        dm.save_exchange(exchange)

        util.write_log(logger,
                       'create a the very beginning of exchange chain. current height: %d' % exchange.exchange.processed_block_height)
        return

    #2 init data from the newest save; get the latest block height
    latest_block_height = openexchangelib.retrieve_latest_block_height()

    #3 if there's no new block to process, exit
    if latest_block_height - exchange.exchange.processed_block_height < 6:
        util.write_log(logger,
                       'no new block to process. exit. current height: %d' % exchange.exchange.processed_block_height)
        return

    #4 check if the previous block is payed (or no need to pay), if not, print error & exit
    if exchange.payout_block_height < exchange.exchange.processed_block_height:
        assert exchange.payout_block_height == exchange.exchange.processed_block_height - 1
        tx = find_pay_out_transaction(exchange.exchange.processed_block_height, exchange.exchange.payment_log_address,
                                      exchange.exchange.open_exchange_address)
        if tx is None:
            util.write_log(logger, 'block %d is still not payed. Will wait for a while. '
                                   'Or is there any problem with our server?' % exchange.exchange.processed_block_height)
            return
        else:
            util.write_log(logger, 'block %d is payed. transaction hash is %s' % (exchange.exchange.processed_block_height, tx))
            exchange.payout_block_height = exchange.exchange.processed_block_height
            exchange.payout_transactions[exchange.exchange.processed_block_height] = tx  # no need to save now

    #5 otherwise, process the new block, pays the payment, save the new market data & exit
    new_block = openexchangelib.retrieve_block(exchange.exchange.processed_block_height + 1)
    assert new_block.hash == exchange.exchange.processed_block_hash

    requests = openexchangelib.process_block(exchange.exchange, new_block, dm.assets_data())
    payments = {}
    for req in requests:
        add_payment(payments, req.related_payments)

    if not payments:  # no need to pay anything
        exchange.payout_block_height = new_block.height
        util.write_log(logger, 'no need to pay block %d' % new_block.height)
    else:
        add_payment(payments, {exchange.exchange.payment_log_address: new_block.height})
        #make payments
        tx_hash = pybit.send_from_address(None, payments, exchange.exchange.open_exchange_address)
        util.write_log(logger, "payment for block %d: transaction hash is %s" % (new_block.height, tx_hash))

    dm.save_exchange(exchange)
    util.write_log(logger, 'a new block is processed. height: %d' % new_block.height)


if __name__ == "__main__":
    process_next_block()
