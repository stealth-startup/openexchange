#do not use types as module name, it conflicts

from openexchangelib import types as oel_types


class DataFileDoesNotExistError(oel_types.OEBaseException):
    pass


class FileAlreadyExistError(oel_types.OEBaseException):
    pass


class PaymentRecordNeedRebuildError(oel_types.OEBaseException):
    pass


class ExchangeServer(object):
    def __init__(self, exchange):
        """
        :type exchange: Exchange
        """
        self.exchange = exchange

        #used assets creation data / re-init data indexes
        self.used_init_data_indexes = set()

