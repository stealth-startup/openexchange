__author__ = 'Rex'

from openexchangelib.types import OEBaseException, Asset, User
from openexchangelib import util
import os


PROJ_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJ_DIR, 'data')
ASSETS_DIR = os.path.join(DATA_DIR, 'assets')
logger = util.get_logger('test_with_fake_data', file_name='fake_data_test.log')


class PybitSettingsError(OEBaseException):
    pass


class OpenExchangeLibSettingsError(OEBaseException):
    pass


def set_up_data():
    asic_miner = Asset(
        total_shares=400000,
        limit_buy_address='asm_limit_buy',
        limit_sell_address='asm_limit_sell',
        market_buy_address='asm_market_buy',
        market_sell_address='asm_market_sell',
        clear_order_address='asm_clear_order',
        transfer_address='asm_transfer',
        pay_address='asm_pay',
        create_vote_address='asm_create_vote',
        vote_address='asm_user_vote',
        state_control_address='asm_state_control',
        issuer_address='asm_issuer',
        users={
            'captain_miao': User(initial_asset=400000)
        }
    )
    util.save_obj(['ASICMINER', asic_miner], os.path.join(ASSETS_DIR, '1'))
    util.write_log(logger, 'ASICMINER data saved')


def check_pybit_settings():
    from pybit import settings as pybit_settings
    if not pybit_settings.USE_FAKE_DATA or not pybit_settings.IGNORE_SEND_FROM_LOCAL:
        raise PybitSettingsError(USE_FAKE_DATA=pybit_settings.USE_FAKE_DATA,
                                 IGNORE_SEND_FROM_LOCAL=pybit_settings.IGNORE_SEND_FROM_LOCAL)
    util.write_log(logger, 'pybit OK')


def check_openexchangelib_settings():
    from openexchangelib import settings as oel_settings
    if not oel_settings.FAKE_DATA:
        raise OpenExchangeLibSettingsError(FAKE_DATA=oel_settings.FAKE_DATA)
    util.write_log(logger, 'OpenExchangeLib OK')


def start():
    """
    """
    import exchange_server

    check_pybit_settings()
    check_openexchangelib_settings()
    set_up_data()

    os.chdir(PROJ_DIR)
    for i in xrange(10):
        exchange_server.process_next_block(1)
    util.write_log(logger, 'All done')



if __name__ == "__main__":
    start()


