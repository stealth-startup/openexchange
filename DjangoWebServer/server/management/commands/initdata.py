#https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#howto-custom-management-commands
from django.core.management.base import NoArgsCommand
import openexchangelib
from openexchangelib import types as oetypes
from server.models import ChainedState, StaticData
import server.data_management as dm


class Command(NoArgsCommand):
    help = 'Initialize ChainedState. Run this command before start the web server.'

    def handle_noargs(self, **options):
        self.stdout.write('getting a new Application object')
        chained_state = super(ChainedState, ChainedState).__new__(ChainedState)
        ChainedState._global_instance = chained_state

        self.stdout.write('initializing the chained_state obj')
        chained_state.exchange = openexchangelib.exchange0()
        chained_state.asset_history = {}
        chained_state.user_history = {}
        chained_state.exchange_history = []
        chained_state.failed_requests = []
        chained_state.recent_trades = {}  # asset_name -> list of TradeItem
        chained_state.order_book = {}  # asset_name -> dict ('ask'->ask_orders_data, 'bid'->bid_orders_data)
        chained_state.chart_data = {}  # asset_name -> list


        #test purpose
        #TODO delete the following test code when finish testing
        chained_state.exchange.state=chained_state.exchange.STATE_RUNNING
        name, asset_data = dm.asset_creation_data(1)
        chained_state.exchange.assets[name] = asset_data
        chained_state.exchange.assets[name].state = oetypes.Asset.STATE_RUNNING

        static_data = super(StaticData, StaticData).__new__(StaticData)
        static_data.asset_description = {'ASICMiner': 'blah blah blah'}
        dm.save_static_data(static_data)


        dm.push_chained_state(chained_state)
        self.stdout.write('chained_state saved')

