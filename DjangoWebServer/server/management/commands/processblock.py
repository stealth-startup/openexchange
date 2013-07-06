#https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#howto-custom-management-commands
from django.core.management.base import NoArgsCommand, CommandError
import openexchangelib
import server.data_management as dm
from openexchangelib import types
from openexchangelib import util
from server.models import UserPayLog


class Command(NoArgsCommand):
    help = 'process one more block (if possible)'

    def handle_noargs(self, **options):
        def display_order_book(raw_order_book):
            """
            :raw_order_book: list of BuyLimitOrder or SellLimitOrder
            """
            def add_item(display_book, unit_price, amount):
                display_book.append([unit_price/100000000, amount, unit_price * amount / 100000000])

            display_book = []
            unit_price = None
            total_amount = 0

            for order in raw_order_book:
                if order.unit_price != unit_price:
                    if unit_price is not None:
                        add_item(display_book, unit_price, total_amount)
                        if len(display_book) >= 50:
                            return display_book
                        else:
                            unit_price = order.unit_price
                            total_amount = order.volume_unfulfilled
                else:
                    total_amount += order.volume_unfulfilled

            if unit_price is not None:
                add_item(display_book, unit_price, total_amount)
            return display_book

        latest_processed_height = dm.data_file_max_index(dm.BLOCK_FOLDER)
        if latest_processed_height is None:
            raise CommandError('ChainedState is not initialized yet')

        latest_block_height = openexchangelib.retrieve_latest_block_height()
        assert latest_block_height >= latest_processed_height

        if latest_block_height == latest_processed_height:
            self.stdout.write('no need to update')
            return

        self.stdout.write('loading the latest ChainedState')
        chained_state = dm.block_data(latest_processed_height)

        retrieve_height = latest_processed_height + 1
        self.stdout.write('retrieving a new block')
        new_block = openexchangelib.retrieve_block(retrieve_height)

        if new_block.previous_hash != chained_state.exchange.processed_block_hash:
            self.stdout.write('blockchain is changed, we fall back one block')
            dm.pop_chained_state()
            return

        self.stdout.write('working on the new block ...')
        requests = openexchangelib.process_block(chained_state.exchange, new_block, dm.assets_data())
        address_book = openexchangelib.address_book(chained_state.exchange)

        self.stdout.write('updating history ...')
        for req in requests:
            assert req.state != types.Request.STATE_NOT_PROCESSED
            if req.state == types.Request.STATE_FATAL:
                chained_state.failed_requests.append(req)
                continue

            user_address = req.transaction.input_address
            asset_name = address_book[user_address][0]

            if isinstance(req, [types.CreateAsset, types.ExchangeStateControl]):
                chained_state.exchange_history.append(req)
            elif isinstance(req,
                            [types.BuyLimitOrder, types.SellLimitOrder, types.BuyMarketOrder, types.SellMarketOrder,
                             types.ClearOrder, types.Transfer, types.VoteRequest]):
                if asset_name not in chained_state.user_history:
                    chained_state.user_history[asset_name] = {}
                if user_address not in chained_state.user_history[asset_name]:
                    chained_state.user_history[asset_name][user_address] = []
                chained_state.user_history[asset_name][user_address].append(req)

                if isinstance(req, [types.BuyLimitOrder, types.SellLimitOrder, types.BuyMarketOrder, types.SellMarketOrder]):
                    if asset_name not in chained_state.recent_trades:
                        chained_state.recent_trades[asset_name] = []
                    chained_state.recent_trades[asset_name] += [ti for ti in req.trade_history if not isinstance(ti, types.CanceledTrade)]
                    chained_state.recent_trades[asset_name] = chained_state.recent_trades[asset_name][-100:]

                    if asset_name not in chained_state.chart_data:
                        chained_state.chart_data[asset_name] = []
                    chained_state.chart_data[asset_name] += [[util.datetime_to_timestamp(ti.timestamp)*1000, ti.unit_price, ti.amount]
                        for ti in req.trade_history if not isinstance(ti, types.CanceledTrade)
                    ]

            elif isinstance(req, [types.CreateVote, types.Pay, types.AssetStateControl]):
                if asset_name not in chained_state.asset_history:
                    chained_state.asset_history[asset_name] = []
                chained_state.asset_history[asset_name].append(req)
                if isinstance(req, types.Pay):
                    for ua, u in chained_state.exchange.assets[asset_name].users.iteritems():
                        if asset_name not in chained_state.user_history:
                            chained_state.user_history[asset_name] = {}
                        if ua not in chained_state.user_history[asset_name]:
                            chained_state.user_history[asset_name][ua] = []
                        chained_state.user_history[asset_name][user_address].append(
                            UserPayLog(req.transaction, req.payer, req.DPS, u.total))

        self.stdout.write('rebuilding order book')
        del chained_state.order_book
        chained_state.order_book = {}

        for asset_name, asset in chained_state.exchange.assets.iteritems():
            if asset.sell_order_book or asset.buy_order_book:
                sell_orders = display_order_book(asset.sell_order_book)
                buy_orders = display_order_book(asset.buy_order_book)
                chained_state.order_book[asset_name] = {'ask': sell_orders, 'bid': buy_orders}

        self.stdout.write('saving the new chained_state')
        dm.push_chained_state(chained_state)
        self.stdout.write('complete. we advanced one block further to %d' % new_block.height)
