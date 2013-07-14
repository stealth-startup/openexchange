#  main logic:
#
#  1 load the latest state.
#  2 load the payment records (block_height -> (payments made, unpaid payments, transaction_hashes)),
#    if damaged, rebuild it via blockchain
#  3 assert state.height in records
#    if unpaid payments is not {}, which means the payment process may go wrong last time, go to 'make_payments'
#    if unpaid is {}, go to 4
#  4 process the next block according to the state, get all processed requests
#  5 update used-init-assets-id according to all the requests
#  6 aggregate all payments according to all the requests
#  7 add payment records [state.height+1] = ({}, unpaid = aggregate payments); save payment records
#  8 update state for the new height; save state;
#  9 while unpaid: (make_payments)
#        make payment using pybit
#        update payments made & unpaid; save payment record

#use cron job to run the server script repeatedly
#cPickle benchmark:
#http://stackoverflow.com/questions/8514020/marshal-dumps-faster-cpickle-loads-faster
#so we should be OK with cPickle for a pretty long time

import openexchangelib
from openexchangelib import util, types as oel_types
import data_management as dm
from ext_types import ExchangeServer, PaymentRecordNeedRebuildError
import pybit
import os


PROJ_DIR = os.path.abspath(os.path.dirname(__file__))
logger = util.get_logger('exchange_server', file_name=os.path.join(PROJ_DIR, 'exchange_server.log'))


def add_payment(all_payments, payments):
    """
    :type all_payments: dict from str to int
    :type payments: dict from str to int
    """
    for address, amount in payments.iteritems():
        assert amount >= 0
        assert isinstance(amount, int)

        if amount == 0:
            continue

        if address in all_payments:
            all_payments[address] += amount
        else:
            all_payments[address] = amount


MAX_PAYMENT_BATCH = 50


def make_payments(payment_records, height, log_address, from_addresses, change_address):
    """
    :type payment_records: list of tuple
    :type height: int
    """
    #make payments (may be multiple times), save payment_records
    paid, unpaid, txs = payment_records[height]
    if not unpaid:
        return

    assert log_address not in unpaid
    batch_n = (len(unpaid) - 1) // MAX_PAYMENT_BATCH + 1

    addresses = unpaid.keys()
    address_batches = [addresses[i * MAX_PAYMENT_BATCH: (i + 1) * MAX_PAYMENT_BATCH] for i in xrange(batch_n)]
    batches = [{address: unpaid[address] for address in l} for l in address_batches ]

    for batch in batches:
        batch[log_address] = height
        tx = pybit.send_from_local(batch, from_addresses=from_addresses, change_address=change_address, fee=0)
        util.write_log(logger, batch=batch, tx=tx)

        for address, amount in batch.iteritems():
            if address == log_address:
                continue
            else:
                del unpaid[address]
                paid[address] = paid.get(address, 0) + amount
                txs.append(tx)
                dm.save_payments(payment_records)


def process_next_block(min_confirmations=6):
    #1 load the latest state
    exchange = dm.pop_exchange()
    if exchange is None:
        #init exchange
        util.write_log(logger, 'creating the beginning of exchange chain.')
        dm.push_exchange(ExchangeServer(openexchangelib.exchange0()))
        #init payment records
        util.write_log(logger, 'creating the initial payment records.')
        dm.initialize_payments()
        util.write_log(logger, 'initial data done. ')
        return

    #2 load the payment records
    try:
        payment_records = dm.load_payments()
    except:
        raise PaymentRecordNeedRebuildError('cannot load payment records, please rebuild the records using '
                                            'transactions in the block chain if necessary')

    #3 assert state.height in records
    #if unpaid payments is not {}, which means the payment process may go wrong last time, go to 'make_payments'
    #if unpaid is {}, go to 4
    assert exchange.exchange.processed_block_height in payment_records
    c_paid, c_unpaid, c_txs = payment_records[exchange.exchange.processed_block_height]
    if c_unpaid != {}:
        util.write_log(logger, 'unpaid payments are non-empty, is there anything go wrong last time?', unpaid=c_unpaid)
        make_payments(payment_records, exchange.exchange.processed_block_height)
        return

    #4 process the next block according to the state, get all processed requests
    latest_block_height = pybit.get_block_count()
    if latest_block_height - exchange.exchange.processed_block_height < min_confirmations:
        util.write_log(logger, 'no need to update')
        return

    util.write_log(logger, 'getting the new block')
    new_block = pybit.get_block_by_height(exchange.exchange.processed_block_height + 1)
    assert new_block.previous_hash == exchange.exchange.processed_block_hash
    util.write_log(logger, 'processing the new block')
    requests = openexchangelib.process_block(exchange.exchange, new_block, dm.assets_data(exchange))

    #5 update used-init-assets-id according to all the requests
    util.write_log(logger, 'updating exchange.used_init_data_indexes')
    for req in requests:
        if isinstance(req, oel_types.CreateAssetRequest) and req.state == oel_types.Request.STATE_OK:
            exchange.used_init_data_indexes.add(req.file_id)
        elif isinstance(req, oel_types.AssetStateControlRequest) and req.state == oel_types.Request.STATE_OK \
            and req.request_state % 10 == 3:
            exchange.used_init_data_indexes.add(req.request_state // 10)

    #6 aggregate all payments according to all the requests
    util.write_log(logger, 'aggregating payments')
    payments = {}
    for req in requests:
        add_payment(payments, req.related_payments)

    #7 add payment records [state.height+1] = ({}, unpaid = aggregate payments); save payment records
    util.write_log(logger, 'adding payments to payment records')
    payment_records[new_block.height] = ({}, payments, [])  # paid, unpaid, txs
    dm.save_payments(payment_records)

    #8 update state for the new height; save state;
    util.write_log(logger, 'saving exchange')
    dm.push_exchange(exchange)

    #9 make payments
    util.write_log(logger, 'making payments')
    make_payments(payment_records, new_block.height,
                  log_address=exchange.exchange.payment_log_address,
                  from_addresses=exchange.exchange.open_exchange_address,
                  change_address=exchange.exchange.open_exchange_address)

    util.write_log(logger, 'all done')


if __name__ == "__main__":
    process_next_block()
