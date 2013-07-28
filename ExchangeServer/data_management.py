from openexchangelib import util
import openexchangelib.settings as oel_settings
import os
from ext_types import DataFileDoesNotExistError, FileAlreadyExistError


data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
ASSETS_FOLDER = os.path.join(data_path, 'assets')
BLOCKS_FOLDER = os.path.join(data_path, 'blocks')
PAYMENTS_FOLDER = os.path.join(data_path, 'payments')
PAYMENTS_FILE_NAME = 'payments'


def load_data(file_name, base):
    assert isinstance(file_name, str)
    file_name = os.path.join(base, file_name)
    if not os.path.isfile(file_name):
        raise DataFileDoesNotExistError(file_name=file_name)
    return util.load_obj(file_name)


def save_data(obj, file_name, base):
    assert isinstance(file_name, str)
    file_name = os.path.join(base, file_name)
    return util.save_obj(obj, file_name)


def asset_creation_data(index):
    """
    :type index: int
    :rtype: tuple of (str, Asset)
    """
    return load_data(str(index), ASSETS_FOLDER)


def asset_reinitialize_data(index):
    """
    different asset should use different index, so there's no need to have asset_name known
    :type index: int
    :rtype: Asset
    """
    return load_data(str(index), ASSETS_FOLDER)


def _data_file_max_index(base):
    indexes = [int(f) for f in os.listdir(base) if os.path.isfile(os.path.join(base, f)) and f.isdigit()]
    if not indexes:
        return None
    else:
        return max(indexes)


def pop_exchange():
    """
    :rtype: ExchangeServer
    """
    max_index = _data_file_max_index(BLOCKS_FOLDER)
    if max_index is None:
        return None
    else:
        return load_data(str(max_index), BLOCKS_FOLDER)


def push_exchange(exchange):
    """
    :type exchange: ExchangeServer
    """
    height = exchange.exchange.processed_block_height
    save_data(exchange, str(height), BLOCKS_FOLDER)


def assets_data(exchange):
    """
    :type exchange: ExchangeServer
    """
    indexes = [int(f) for f in os.listdir(ASSETS_FOLDER)
               if os.path.isfile(os.path.join(ASSETS_FOLDER, f)) and f.isdigit()]
    return {index: util.load_obj(os.path.join(ASSETS_FOLDER, str(index)))
            for index in set(indexes) - exchange.used_init_data_indexes}


def load_payments():
    return load_data(PAYMENTS_FILE_NAME, PAYMENTS_FOLDER)


def save_payments(payments, over_written=True):
    if not over_written:
        file_name = os.path.join(PAYMENTS_FOLDER, PAYMENTS_FILE_NAME)
        if os.path.isfile(file_name):
            raise FileAlreadyExistError(file_name=file_name)

    return save_data(payments, PAYMENTS_FILE_NAME, PAYMENTS_FOLDER)


def initialize_payments():
    from ext_types import PaymentRecord

    save_payments({
        #block height -> PaymentRecord
        oel_settings.EXCHANGE_INIT_BLOCK_HEIGHT: PaymentRecord(),
    }, False)