from openexchangelib.types import OEBaseException


class DataFileNotExistError(OEBaseException):
    pass


class FileAlreadyExistError(OEBaseException):
    pass


class PaymentRecordNeedRebuildError(OEBaseException):
    pass


class ExchangeServer(object):
    def __init__(self, exchange):
        """
        :type exchange: Exchange
        """
        self.exchange = exchange

        #used assets creation data / re-init data indexes
        self.used_init_data_indexes = set()

