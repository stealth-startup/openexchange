__author__ = 'Rex'


from openexchangelib.types import OEBaseException
import os


ASICMINER_CREATION_FILE_ID = 1
PROJ_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJ_DIR, 'data')
ASSET_DIR = os.path.join(DATA_DIR, 'assets')


class AssetFolderNotEmptyError(OEBaseException):
    pass


class PybitSettingsError(OEBaseException):
    pass


class OpenExchangeLibSettingsError(OEBaseException):
    pass

def set_up_asicminer():
    import openexchangelib.types as oel_types
    from openexchangelib import util

    asic_miner = oel_types.Asset(
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
        issuer_address='asm_issuer'
    )
    asic_miner.users = {
        'captain_miao': 400000
    }
    #make sure that asset folder is empty
    current_ids = [int(f) for f in os.listdir(ASSET_DIR)
                   if os.path.isfile(os.path.join(ASSET_DIR, f)) and f.isdigit()]
    if current_ids:
        raise AssetFolderNotEmptyError('please back up your data before running this test')
    full_name = os.path.join(ASSET_DIR, str(ASICMINER_CREATION_FILE_ID))
    util.save_obj(['ASICMINER', asic_miner], full_name)

    return asic_miner


def check_pybit_settings():
    from pybit import settings as pybit_settings
    if not pybit_settings.USE_FAKE_DATA or not pybit_settings.IGNORE_SEND_FROM_LOCAL:
        raise PybitSettingsError(USE_FAKE_DATA=pybit_settings.USE_FAKE_DATA,
                                 IGNORE_SEND_FROM_LOCAL=pybit_settings.IGNORE_SEND_FROM_LOCAL)


def check_openexchangelib_settings():
    import openexchangelib.settings as oel_settings
    if not oel_settings.FAKE_DATA:
        raise OpenExchangeLibSettingsError(FAKE_DATA=oel_settings.FAKE_DATA)


def start(n):
    """
    :type n: int
    """
    check_pybit_settings()
    check_openexchangelib_settings()
    set_up_asicminer()

    os.chdir(PROJ_DIR)
    os.system('python manage.py initdata')

    for i in xrange(n):
        os.system('python manage.py processblock')

    os.system('python manage.py runserver')


if __name__ == "__main__":
    import sys
    assert len(sys.argv)==2
    n = int(sys.argv[1])
    start(n)


