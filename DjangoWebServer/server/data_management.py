from openexchangelib import util
from openexchangelib.types import OEBaseException
import os

data_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'data')
ASSET_FOLDER = os.path.join(data_path, 'assets')
BLOCK_FOLDER = os.path.join(data_path, 'block')
BLOCK144_FOLDER = os.path.join(data_path, 'block144')


class AssetDataFileNotExistError(OEBaseException):
    pass


class StaticDataFileNotExistError(OEBaseException):
    pass


def load_data(index, base):
    file_name = os.path.join(base, str(index))
    if not os.path.isfile(file_name):
        raise AssetDataFileNotExistError(index = index)
    return util.load_obj(file_name)


def save_data(obj, index, base):
    file_name = os.path.join(base, str(index))
    return util.save_obj(obj, file_name)


def asset_creation_data(index):
    """
    :type index: int
    :rtype: tuple of (str, Asset)
    """
    return load_data(index, ASSET_FOLDER)


def asset_initialize_data(index):
    """
    different asset should use different index, so there's no need to have asset_name known
    :type index: int
    :rtype: Asset
    """
    return load_data(index, ASSET_FOLDER)


def block_data(index):
    return load_data(index, BLOCK_FOLDER)


def block144_data(index):
    return load_data(index, BLOCK144_FOLDER)


def data_file_max_index(base):
    indexes = [int(f) for f in os.listdir(base) if os.path.isfile(os.path.join(base, f)) and f.isdigit()]
    if not indexes:
        return None
    else:
        return max(indexes)


def latest_chained_state():
    """
    :rtype: ChainedState
    """
    max_index = data_file_max_index(BLOCK_FOLDER)
    if max_index is None:
        return None
    else:
        return block_data(max_index)


def push_chained_state(chained_state):
    """
    :type chained_state: ChainedState
    """
    logger = util.get_logger('web_server')

    height = chained_state.exchange.processed_block_height
    save_data(chained_state, height, BLOCK_FOLDER)

    if height % 144 == 0:
        save_data(chained_state, height, BLOCK144_FOLDER)
        util.write_log(logger, 'chained_state is also saved to %s' % BLOCK144_FOLDER)

    height_to_clean = height - 144  # only keep at most 144 files in block folder
    file_to_clean = os.path.join(BLOCK_FOLDER, str(height_to_clean))
    if os.path.isfile(file_to_clean):
        os.remove(file_to_clean)
        util.write_log(logger, '%d is removed' % height_to_clean)

    util.write_log(logger, 'chained_state saved. height: %d' % chained_state.exchange.processed_block_height)


def pop_chained_state():
    """
    """
    logger = util.get_logger('web_server')

    height = data_file_max_index(BLOCK_FOLDER)

    if height % 144 == 0 and os.path.isfile(os.path.join(BLOCK144_FOLDER, str(height))):
        os.remove(os.path.join(BLOCK144_FOLDER, str(height)))
        util.write_log(logger, 'height %d is removed from %s' % (height, BLOCK144_FOLDER))

    os.remove(os.path.join(BLOCK_FOLDER, str(height)))
    util.write_log(logger, 'height %d is removed from %s' % (height, BLOCK_FOLDER))


def load_static_data():
    if not os.path.isfile(os.path.join(data_path, 'static_data')):
        raise StaticDataFileNotExistError()
    else:
        return util.load_obj(os.path.join(data_path, 'static_data'))


def assets_data():
    indexes = [int(f) for f in os.listdir(ASSET_FOLDER) if os.path.isfile(os.path.join(ASSET_FOLDER, f)) and f.isdigit()]
    return {index: util.load_obj(os.path.join(ASSET_FOLDER, str(index))) for index in indexes}