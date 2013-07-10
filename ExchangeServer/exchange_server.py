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
from types import ExchangeServer, PaymentRecordNeedRebuildError
import pybit


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


def make_payments(payment_records, height):
    """
    :type payment_records: list of tuple
    :type height: int
    """
    #TODO
    #make payments (may be multiple times), save payment_records
    #remember to add log_address when making payments
    pass


def process_next_block():
    logger = util.get_logger('exchange_server')
    #1 load the latest state
    exchange = dm.pop_exchange()
    if exchange is None:
        #init exchange
        util.write_log(logger, 'creating the beginning of exchange chain.')
        dm.push_exchange(ExchangeServer(openexchangelib.exchange0()))
        util.write_log(logger, 'exchange saved. height: %d' % exchange.exchange.processed_block_height)
        #init payment records
        util.write_log(logger, 'creating the initial payment records.')
        dm.initialize_payments()
        util.write_log(logger, 'initial payment records saved. ')
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
    if latest_block_height - exchange.exchange.processed_block_height < 6:
        util.write_log(logger, 'no need to update')
        return

    util.write_log(logger, 'getting the new block')
    new_block = pybit.get_block_by_height(exchange.exchange.processed_block_height+1)
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
    util.write_log('adding payments to payment records')
    payment_records[new_block.height] = ({}, payments, [])  # paid, unpaid, txs
    dm.save_payments(payment_records)

    #8 update state for the new height; save state;
    util.write_log('saving exchange')
    dm.push_exchange(exchange)

    #9 make payments
    util.write_log('making payments')
    make_payments(payment_records, new_block.height)

    util.write_log('all done')


if __name__ == "__main__":
    process_next_block()
