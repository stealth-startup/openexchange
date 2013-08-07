#https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#howto-custom-management-commands
from django.core.management.base import NoArgsCommand
from server.models import StaticData
import openexchangelib.types as oel_types
from server import data_management as dm


class Command(NoArgsCommand):
    help = 'Generate non-chained data.'

    def handle_noargs(self, **options):
        self.stdout.write('Generating non-chained data ...')

        self.stdout.write('Generating static_data ...')
        static_data = StaticData()
        dm.save_static_data(static_data)
        self.stdout.write('static_data saved...')

        self.stdout.write('Generating asset data - TEST')
        ASSET_TEST = oel_types.Asset(
            total_shares=100000,
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
            issuer_address='mq2LLPrar9vkUMnzcNtAEJJa37PKfZisTG',
            users={
                'mmy8qpLmZoxe1rSynrnx7k1XwHDm3BKpeQ': oel_types.User(initial_asset=100000),  # main holder
            }
        )

        dm.save_asset_data(['TEST', ASSET_TEST], 1)
        self.stdout.write('TEST asset saved')

        self.stdout.write('Generating asset data - TEST2')
        ASSET_TEST2 = oel_types.Asset(
            total_shares=800000,
            clear_order_address="moxT1cTs2Jn6Sodhv53QpxQkqKaVKkgSnv",
            create_vote_address="n2uvtDcDLMrKx4t5cfjmV4cSnmhNqXeKeb",
            issuer_address="n4pNgZx4J4Z2pyCAcNeMKddYJ7bz2qbGGP",
            limit_buy_address="mt6sD1bHBQEpJ9tK2dEaVMT5xdqwAovvJr",
            limit_sell_address="mtwfXuFjPgFdWumC92iAXWMJu2ACt1uHNe",
            market_buy_address="mh6cnop2SFrpvJAYxTJ2Giw6ZrvjTE4cf8",
            market_sell_address="mpyggDyWALrLihXKeZ1u3FShj2ihqLhad3",
            pay_address="mgWFoZqFEsCXGDkiyiZhMz5XXJ8zf17Pc9",
            state_control_address="myERW1mFdFLpUK9swMRULCwUqhkjCsNsEx",
            transfer_address="mp81MKYpMgCsBfA2pZ3VgHwsMwrh81dvvR",
            vote_address="mh5K3WWnKvZe48xt2VWP1xzVUMKprVmoo8",
            users={
                'mmy8qpLmZoxe1rSynrnx7k1XwHDm3BKpeQ': oel_types.User(initial_asset=800000),  # main holder
            }
        )

        dm.save_asset_data(['TEST2', ASSET_TEST2], 2)
        self.stdout.write('TEST2 asset saved')

        self.stdout.write('all done')

