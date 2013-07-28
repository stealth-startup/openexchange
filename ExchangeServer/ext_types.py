#do not use types as module name, it conflicts

from openexchangelib import types as oel_types
from pybit.types import Printable


class DataFileDoesNotExistError(oel_types.OEBaseException):
    pass


class FileAlreadyExistError(oel_types.OEBaseException):
    pass


class PaymentRecordNeedRebuildError(oel_types.OEBaseException):
    pass


class PaymentInconsistentError(oel_types.OEBaseException):
    pass


class PaymentRecord(Printable):
    def __init__(self, paid=None, unpaid=None, transactions=None):
        """
        :type paid: dict from str to int
        :type unpaid: dict from str to int
        :type transactions: list of dict
        :param transactions: list of {'hash': tx_hash, 'signed_tx': signed_transaction}
        """
        self.paid = paid if paid is not None else {}
        self.unpaid = unpaid if unpaid is not None else {}
        self.transactions = transactions if transactions is not None else []


class ExchangeServer(object):
    def __init__(self, exchange):
        """
        :type exchange: Exchange
        """
        self.exchange = exchange

        #used assets creation data / re-init data indexes
        self.used_init_data_indexes = set()

