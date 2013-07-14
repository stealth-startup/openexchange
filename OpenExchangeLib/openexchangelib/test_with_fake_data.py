__author__ = 'Rex'


from openexchangelib import types, util, settings
import os


PROJ_DIR = os.path.abspath(os.path.dirname(__file__))


class PybitSettingsError(types.OEBaseException):
    pass


class OpenExchangeLibSettingsError(types.OEBaseException):
    pass


def set_up_asicminer():
    return types.Asset(
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
            'captain_miao': types.User(initial_asset=400000)
        }
    )


def check_pybit_settings():
    from pybit import settings as pybit_settings
    if not pybit_settings.USE_FAKE_DATA or not pybit_settings.IGNORE_SEND_FROM_LOCAL:
        raise PybitSettingsError(USE_FAKE_DATA=pybit_settings.USE_FAKE_DATA,
                                 IGNORE_SEND_FROM_LOCAL=pybit_settings.IGNORE_SEND_FROM_LOCAL)


def check_openexchangelib_settings():
    if not settings.FAKE_DATA:
        raise OpenExchangeLibSettingsError(FAKE_DATA=settings.FAKE_DATA)


def start():
    """
    """
    import openexchangelib
    import pybit

    check_pybit_settings()
    check_openexchangelib_settings()
    asset_data = {1: ['ASICMINER', set_up_asicminer()]}

    logger = util.get_logger('test_use_fake_data', file_name='fake_data_test.log')
    exchange = openexchangelib.exchange0()
    util.write_log(logger, exchange0=exchange, blank_lines=2)

    block_n = pybit.get_block_count()
    util.write_log(logger, block_n=block_n, blank_lines=2)

    for i in xrange(1, block_n+1):
        block = pybit.get_block_by_height(i)
        util.write_log(logger, i=i, block=block, blank_lines=2)

        requests = openexchangelib.process_block(exchange, block, asset_data)
        util.write_log(logger, requests=requests, blank_lines=2)

        util.write_log(logger, exchange=exchange, blank_lines=2)

    util.write_log(logger, 'All done')


if __name__ == "__main__":
    start()


