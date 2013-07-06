from openexchangelib.types import Asset, User
from openexchangelib import util


def create_AM_init_data():
    asset_name = "ASICMiner"
    asicminer = Asset(
        10000,
        limit_buy_address='mptmhH4UzgS3cJ35qmjqNaGWa15UPoE3fy',
        limit_sell_address='mmYt5cVNcFmrDvSBf6erYYeypnZTH4c8Xk',
        market_buy_address='mrbmg4C1dh1CvBDNPKEYGSYnkh6kDZ48QW',
        market_sell_address='miyMq1JH3e2kEjRSXRt8W9CgXkbwxXw35A',
        clear_order_address='mvbF8xwEtKjGC96HyuHZxSnXyoYgSZhaFG',
        transfer_address='mrPXUoy1Pv7WRKxtkRXgKcikVAMQiiCX8b',
        pay_address='mz2Qtbi7aZi6tduLy12bQZk7TT7FDk8E8T',
        create_vote_address='n1w3qs2zHgFwH8UCtWH7TNV389PXfaCY6Z',
        vote_address='mvP5ecwKh13L82HELUKpNjK8YCVnsH8J8h',
        state_control_address='mhpxNSM8AjCpRvDXry7foWbB6Ti5BCShRF',
        issuer_address='mq2LLPrar9vkUMnzcNtAEJJa37PKfZisTG'
    )
    user=User()
    user.available=10000
    user.total=10000
    asicminer.users['mmy8qpLmZoxe1rSynrnx7k1XwHDm3BKpeQ']=user
    util.save_obj( (asset_name,asicminer) , '1')


create_AM_init_data()