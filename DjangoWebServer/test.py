__author__ = 'Rex'


import pybit.settings as pybit_settings
import pybit.data as pybit_types
import openexchangelib.types as oel_types
import openexchangelib.settings as oel_settings
from openexchangelib import util
from openexchangelib.types import OEBaseException
import os


ASICMINER_CREATION_FILE_ID = 1


class AssetFolderNotEmptyError(OEBaseException):
    pass


data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
ASSET_FOLDER = os.path.join(data_path, 'assets')


def set_up_openexchangelib():
    oel_settings.EXCHANGE_INIT_BLOCK_HEIGHT = 1
    oel_settings.EXCHANGE_INIT_BLOCK_HASH = str(oel_settings.EXCHANGE_INIT_BLOCK_HEIGHT)
    oel_settings.EXCHANGE_STATE_CONTROL_ADDRESS = 'xch_state_control'
    oel_settings.EXCHANGE_CREATE_ASSET_ADDRESS = 'xch_create_asset'
    oel_settings.EXCHANGE_OPEN_EXCHANGE_ADDRESS = 'xch_open_exchange'
    oel_settings.EXCHANGE_PAYMENT_LOG_ADDRESS = 'xch_payment_log'


def set_up_asicminer():
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
    current_ids = [int(f) for f in os.listdir(ASSET_FOLDER)
                   if os.path.isfile(os.path.join(ASSET_FOLDER, f)) and f.isdigit()]
    if current_ids:
        raise AssetFolderNotEmptyError('please back up your data before running this test')
    full_name = os.path.join(ASSET_FOLDER, str(ASICMINER_CREATION_FILE_ID))
    util.save_obj(['ASICMINER', asic_miner])

    return asic_miner

def check_pybit_settings():




