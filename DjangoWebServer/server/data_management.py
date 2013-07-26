from openexchangelib import util
from openexchangelib.types import OEBaseException
import os


def ensure_dir(dir_path):
    """
    :type dir_path: str
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


data_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data')
ASSET_FOLDER = os.path.join(data_path, 'assets')
BLOCK_FOLDER = os.path.join(data_path, 'block')

ensure_dir(ASSET_FOLDER)
ensure_dir(BLOCK_FOLDER)


class FileNotExistError(OEBaseException):
    pass


def load_data(file_name, base):
    """
    :type file_name: str
    :type base: str
    """
    full_name = os.path.join(base, file_name)
    if not os.path.isfile(full_name):
        raise FileNotExistError(fname=file_name)
    return util.load_obj(full_name)


def save_data(obj, file_name, base):
    """
    :type file_name: str
    :type base: str
    """
    assert isinstance(file_name, str)
    assert isinstance(base, str)

    full_name = os.path.join(base, file_name)
    return util.save_obj(obj, full_name)


def remove_data(file_name, base, silent=True):
    """
    :type file_name: str
    :type base: str
    """
    full_name = os.path.join(base, file_name)
    if not os.path.isfile(full_name):
        if not silent:
            raise FileNotExistError(fname=file_name)
        return False
    else:
        os.remove(full_name)
        return True


def data_file_max_index(base):
    indexes = [int(f) for f in os.listdir(base) if os.path.isfile(os.path.join(base, f)) and f.isdigit()]
    if not indexes:
        return None
    else:
        return max(indexes)


def pop_chained_state(remove=False):
    """
    :rtype: ChainedState
    """
    max_index = data_file_max_index(BLOCK_FOLDER)
    if max_index is None:
        return None
    else:
        data = load_data(str(max_index), BLOCK_FOLDER)
        if remove:
            remove_data(str(max_index), BLOCK_FOLDER)
        return data



def push_chained_state(chained_state):
    """
    :type chained_state: ChainedState
    """
    height = chained_state.exchange.processed_block_height
    save_data(chained_state, str(height), BLOCK_FOLDER)


def load_static_data():
    return load_data('static_data', data_path)


def save_static_data(static_data):
    return save_data(static_data, 'static_data', data_path)


def assets_data(chained_state):
    indexes = [int(f) for f in os.listdir(ASSET_FOLDER)
               if os.path.isfile(os.path.join(ASSET_FOLDER, f)) and f.isdigit()]
    return {i: util.load_obj(os.path.join(ASSET_FOLDER, str(i))) for i in set(indexes)-chained_state.used_asset_init_ids}