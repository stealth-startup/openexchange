from types import *
from pybit.types import Transaction

OneHundredMillion = 100000000


################################# some utility functions for request handlers
def _add_payment(request, payments):
    """
    :type request: Request
    :type payments: dict from str to int
    """
    for address, amount in payments.iteritems():
        assert amount >= 0
        if amount == 0:
            continue
        request.related_payments[address] = amount + request.related_payments.get(address, 0)


def _place_buy_limit_order(buy_order_book, buy_order):
    """
    since we execute the requests in the order of their transactions, so we don't need timestamp for sorting.
    in fact, their incoming order is more trustworthy than their timestamp since timestamp could be manipulated
    the buy_order_book is sorted in descending order by unit price; if two requests have the same unit price, the new
    one should be the latter
    TODO: can improve time efficiency by binary search
    :type buy_order_book: list of BuyLimitOrderRequest
    :type buy_order: BuyLimitOrderRequest
    :rtype : None
    """
    loc = None
    for i, buy_order_i in enumerate(buy_order_book):
        if buy_order_i.unit_price < buy_order.unit_price:
            loc = i
            break

    if loc is None:
        buy_order_book.append(buy_order)
    else:
        buy_order_book.insert(loc, buy_order)


def _place_sell_limit_order(sell_order_book, sell_order):
    """
    since we execute the requests in the order of their transactions, so we don't need timestamp for sorting.
    in fact, their incoming order is more trustworthy than their timestamp since timestamp could be manipulated
    the sell_order_book is sorted in ascending order by unit price; if two requests have the same unit price, the new
    one should be the latter
    TODO: can improve time efficiency by binary search
    :type sell_order_book: list of SellLimitOrderRequest
    :type sell_order: SellLimitOrderRequest
    :rtype : None
    """
    loc = None
    for i, sell_order_i in enumerate(sell_order_book):
        if sell_order_i.unit_price > sell_order.unit_price:
            loc = i
            break

    if loc is None:
        sell_order_book.append(sell_order)
    else:
        sell_order_book.insert(loc, sell_order)


def _trade_general(buy_request, sell_request, buyer, seller, unit_price, volume, timestamp, initiate_action):
    """
    manipulate asset record and trade history for users. will not touch anything with payments.
    return TradeItem
    :type buy_request: BuyLimitOrderRequest or BuyMarketOrderRequest
    :type sell_request: SellLimitOrderRequest or SellMarketOrderRequest
    :type buyer: User
    :type seller: User
    :type unit_price: int
    :type volume: int
    :type timestamp: datetime
    :type initiate_action: int
    :param initiate_action: TradeItem.TRADE_TYPE_BUY or TradeItem.TRADE_TYPE_SELL
    """
    assert buyer.available >= 0
    assert buyer.total >= 0
    assert seller.total - seller.available >= volume
    assert seller.available >= 0

    if isinstance(buy_request, BuyLimitOrderRequest):
        buy_request.volume_unfulfilled -= volume
    else:
        assert isinstance(buy_request, BuyMarketOrderRequest)
        buy_request.total_price_unfulfilled -= unit_price * volume
        buy_request.volume_fulfilled += volume

    if isinstance(sell_request, SellLimitOrderRequest):
        sell_request.volume_unfulfilled -= volume
    else:
        assert isinstance(sell_request, SellMarketOrderRequest)
        sell_request.volume_unfulfilled -= volume
        sell_request.price_total_sold += unit_price * volume

    buy_request.trade_history.append(TradeItem(unit_price, volume, timestamp, TradeItem.TRADE_TYPE_BUY))
    sell_request.trade_history.append(TradeItem(unit_price, volume, timestamp, TradeItem.TRADE_TYPE_SELL))

    if isinstance(buy_request, BuyLimitOrderRequest) and initiate_action == TradeItem.TRADE_TYPE_BUY:
        buy_request.immediate_executed_trades.append(TradeItem(unit_price, volume, timestamp, TradeItem.TRADE_TYPE_BUY))
    if isinstance(sell_request, SellLimitOrderRequest) and initiate_action == TradeItem.TRADE_TYPE_SELL:
        sell_request.immediate_executed_trades.append(TradeItem(unit_price, volume, timestamp, TradeItem.TRADE_TYPE_SELL))

    buyer.available += volume
    buyer.total += volume

    seller.total -= volume


class InitDataError(OEBaseException):
    pass


################################### handlers
def create_asset(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    exchange = kwargs['exchange']
    sbtc_amount = kwargs['sbtc_amount']
    n = sbtc_amount % OneHundredMillion
    req = CreateAssetRequest(transaction, service_address, block_timestamp, n)

    if exchange.open_exchange_address not in transaction.input_addresses:
        req.state = Request.STATE_FATAL
        req.message = CreateAssetRequest.MSG_INPUT_ADDRESS_NOT_LEGIT
    else:
        asset_name, new_asset = kwargs['asset_init_data'][n]
        if not (isinstance(asset_name, str) and isinstance(new_asset, Asset) and new_asset.state == Asset.STATE_PAUSED):
            raise InitDataError(asset_name=asset_name, new_asset=new_asset, new_asset_state=new_asset.state)

        if asset_name in exchange.assets:
            req.state = Request.STATE_FATAL
            req.message = CreateAssetRequest.MSG_ASSET_ALREADY_REGISTERED
        else:
            req.state = Request.STATE_OK
            exchange.assets[asset_name] = new_asset

    return req


def exchange_state_control(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    exchange = kwargs['exchange']
    request_state = kwargs['sbtc_amount'] % OneHundredMillion
    req = ExchangeStateControlRequest(transaction, service_address, block_timestamp, request_state)

    if exchange.open_exchange_address not in transaction.input_addresses:
        req.state = Request.STATE_FATAL
        req.message = ExchangeStateControlRequest.MSG_INPUT_ADDRESS_NOT_LEGIT
    elif request_state not in [ExchangeStateControlRequest.STATE_PAUSE, ExchangeStateControlRequest.STATE_RESUME]:
        req.state = Request.STATE_FATAL
        req.message = ExchangeStateControlRequest.MSG_STATE_NOT_SUPPORTED
    else:
        if request_state == ExchangeStateControlRequest.STATE_RESUME:
            exchange.state = Exchange.STATE_RUNNING
        else:
            assert request_state == ExchangeStateControlRequest.STATE_PAUSE
            exchange.state = Exchange.STATE_PAUSED

        req.state = Request.STATE_OK

    return req


def limit_buy(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, volume, sell_order):
        """
        :type req: BuyLimitOrderRequest
        :type volume: int
        :type sell_order: SellLimitOrderRequest
        """
        unit_price = sell_order.unit_price
        assert isinstance(unit_price, int)
        asset = kwargs['asset']

        buyer = asset.users.get(req.user_address)
        assert isinstance(buyer, User)

        seller = asset.users.get(sell_order.user_address)
        assert isinstance(seller, User)

        _trade_general(req, sell_order, buyer, seller, unit_price, volume, block_timestamp, TradeItem.TRADE_TYPE_BUY)

        #refund to buyer
        _add_payment(req, {req.user_address: (req.unit_price - unit_price) * volume})
        #withdraw to seller
        _add_payment(req, {sell_order.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #buyer_address
    buyer_address = transaction.input_addresses[0]

    #volume
    sbtc_amount = kwargs['sbtc_amount']
    volume = sbtc_amount % 10000

    #unit_price
    unit_price = (sbtc_amount - volume) // volume if volume != 0 else None

    #state and message
    state = Request.STATE_OK
    message = None

    if volume == 0:
        state = Request.STATE_FATAL
        message = BuyLimitOrderRequest.MSG_ZERO_VOLUME
    elif unit_price * volume != sbtc_amount - volume or unit_price < 10000 or unit_price % 10000 != 0:
        state = Request.STATE_FATAL
        message = BuyLimitOrderRequest.MSG_UNIT_PRICE_ILLEGIT

    #buyer and order index
    if buyer_address not in asset.users:
        asset.users[buyer_address] = User()
    buyer = asset.users[buyer_address]

    if state == Request.STATE_OK:
        buyer.order_counter += 1
        order_index = buyer.order_counter
    else:
        order_index = None

    req = BuyLimitOrderRequest(transaction, service_address, block_timestamp, order_index, volume, unit_price)

    if state != Request.STATE_OK:
        req.state = state
        req.message = message
        return req
    else:  # start processing limit buy
        buyer.active_orders[order_index] = req

        #change
        _add_payment(req, {buyer_address: volume})

        while True:
            if asset.sell_order_book and asset.sell_order_book[0].unit_price <= req.unit_price:  # can buy something
                if asset.sell_order_book[0].volume_unfulfilled >= req.volume_unfulfilled:  # req is fully fulfilled
                    _trade(req, req.volume_unfulfilled, asset.sell_order_book[0])
                    del buyer.active_orders[req.order_index]

                    if asset.sell_order_book[0].volume_unfulfilled == 0:  # two orders both fulfilled
                        del asset.users[asset.sell_order_book[0].user_address].active_orders[
                            asset.sell_order_book[0].order_index]
                        del asset.sell_order_book[0]

                    break
                else:  # only the sell order is fully fulfilled
                    _trade(req, asset.sell_order_book[0].volume_unfulfilled, asset.sell_order_book[0])
                    del asset.users[asset.sell_order_book[0].user_address].active_orders[
                        asset.sell_order_book[0].order_index]
                    del asset.sell_order_book[0]
            else:  # can not buy anything
                _place_buy_limit_order(asset.buy_order_book, req)
                break

        req.state = BuyLimitOrderRequest.STATE_OK
        return req


def limit_sell(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, volume, buy_order):
        """
        :type req: SellLimitOrderRequest
        :type volume: int
        :type buy_order: BuyLimitOrderRequest
        """
        unit_price = buy_order.unit_price
        assert isinstance(unit_price, int)
        asset = kwargs['asset']

        seller = asset.users.get(req.user_address)
        assert isinstance(seller, User)

        buyer = asset.users.get(buy_order.user_address)
        assert isinstance(buyer, User)

        _trade_general(buy_order, req, buyer, seller, unit_price, volume, block_timestamp, TradeItem.TRADE_TYPE_SELL)

        #withdraw to seller
        _add_payment(req, {req.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #seller_address
    seller_address = transaction.input_addresses[0]

    #volume
    sbtc_amount = kwargs['sbtc_amount']
    volume = sbtc_amount % 10000

    #unit_price
    unit_price = sbtc_amount - volume

    #state and message
    state = Request.STATE_OK
    message = None

    #user
    seller = asset.users.get(seller_address)

    if volume == 0:
        state = Request.STATE_FATAL
        message = SellLimitOrderRequest.MSG_ZERO_VOLUME
    elif unit_price == 0:
        state = Request.STATE_FATAL
        message = SellLimitOrderRequest.MSG_UNIT_PRICE_ILLEGIT
    elif seller is None:
        state = Request.STATE_FATAL
        message = SellLimitOrderRequest.MSG_USER_DOES_NOT_EXISTS
    elif seller.available < volume:
        state = Request.STATE_FATAL
        message = SellLimitOrderRequest.MSG_NOT_ENOUGH_ASSET

    if state == Request.STATE_OK:
        seller.order_counter += 1
        order_index = seller.order_counter
    else:
        order_index = None

    req = SellLimitOrderRequest(transaction, service_address, block_timestamp, order_index, volume, unit_price)

    if state != Request.STATE_OK:
        req.state = state
        req.message = message
        return req
    else:  # start processing limit sell
        seller.active_orders[order_index] = req
        seller.available -= volume

        #change
        _add_payment(req, {seller_address: sbtc_amount})

        while True:
            if asset.buy_order_book and asset.buy_order_book[0].unit_price >= req.unit_price:  # can sell something
                if asset.buy_order_book[0].volume_unfulfilled >= req.volume_unfulfilled:  # req is fully fulfilled
                    _trade(req, req.volume_unfulfilled, asset.buy_order_book[0])
                    del seller.active_orders[req.order_index]

                    if asset.buy_order_book[0].volume_unfulfilled == 0:  # two orders both fulfilled
                        del asset.users[asset.buy_order_book[0].user_address].active_orders[
                            asset.buy_order_book[0].order_index]
                        del asset.buy_order_book[0]

                    break
                else:  # only the buy order is fully fulfilled
                    _trade(req, asset.buy_order_book[0].volume_unfulfilled, asset.buy_order_book[0])
                    del asset.users[asset.buy_order_book[0].user_address].active_orders[
                        asset.buy_order_book[0].order_index]
                    del asset.buy_order_book[0]
            else:  # can not sell anything
                _place_sell_limit_order(asset.sell_order_book, req)
                break

        req.state = Request.STATE_OK
        return req


def market_buy(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, sell_order):
        """
        :type req: BuyMarketOrderRequest
        :type sell_order: SellLimitOrderRequest
        """
        unit_price = sell_order.unit_price
        assert isinstance(unit_price, int)
        asset = kwargs['asset']

        buyer = asset.users.get(req.user_address)
        assert isinstance(buyer, User)

        seller = asset.users.get(sell_order.user_address)
        assert isinstance(seller, User)

        volume = min(req.total_price_unfulfilled // unit_price, sell_order.volume_unfulfilled)
        assert volume > 0

        _trade_general(req, sell_order, buyer, seller, unit_price, volume, block_timestamp, TradeItem.TRADE_TYPE_BUY)

        #withdraw to seller
        _add_payment(req, {sell_order.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #buyer_address
    buyer_address = transaction.input_addresses[0]

    #unit_price
    total_price = kwargs['sbtc_amount']

    #state and message
    state = Request.STATE_OK
    message = None

    if total_price == 0:  # this should never trigger
        state = Request.STATE_FATAL
        message = BuyMarketOrderRequest.MSG_ZERO_TOTAL_PRICE

    #user and order index
    if buyer_address not in asset.users:
        asset.users[buyer_address] = User()

    req = BuyMarketOrderRequest(transaction, service_address, block_timestamp, total_price)

    if state != Request.STATE_OK:
        req.state = state
        req.message = message
        return req
    else:  # start processing limit buy
        while True:
            if asset.sell_order_book and asset.sell_order_book[
                0].unit_price <= req.total_price_unfulfilled:  # can buy something
                if asset.sell_order_book[0].volume_unfulfilled * asset.sell_order_book[
                    0].unit_price >= req.total_price_unfulfilled:  # req is fully fulfilled
                    _trade(req, asset.sell_order_book[0])

                    if asset.sell_order_book[0].volume_unfulfilled == 0:  # two orders both fulfilled
                        del asset.users[asset.sell_order_book[0].user_address].active_orders[
                            asset.sell_order_book[0].order_index]
                        del asset.sell_order_book[0]

                    break
                else:  # only the sell order is fully fulfilled
                    _trade(req, asset.sell_order_book[0])
                    del asset.users[asset.sell_order_book[0].user_address].active_orders[
                        asset.sell_order_book[0].order_index]
                    del asset.sell_order_book[0]
            else:  # can not buy anything
                break

        #add change payments
        _add_payment(req, {req.user_address: req.total_price_unfulfilled})

        req.state = BuyMarketOrderRequest.STATE_OK
        return req


def market_sell(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, buy_order):
        """
        :type req: SellMarketOrderRequest
        :type buy_order: BuyLimitOrderRequest
        """
        unit_price = buy_order.unit_price
        assert isinstance(unit_price, int)
        asset = kwargs['asset']

        seller = asset.users.get(req.user_address)
        assert isinstance(seller, User)

        buyer = asset.users.get(buy_order.user_address)
        assert isinstance(buyer, User)

        volume = min(buy_order.volume_unfulfilled, req.volume_unfulfilled)

        _trade_general(buy_order, req, buyer, seller, unit_price, volume, block_timestamp, TradeItem.TRADE_TYPE_SELL)

        #withdraw to seller
        _add_payment(req, {req.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #seller_address
    seller_address = transaction.input_addresses[0]

    #volume
    sbtc_amount = kwargs['sbtc_amount']
    volume = sbtc_amount % OneHundredMillion

    #state and message
    state = Request.STATE_OK
    message = None

    #user
    seller = asset.users.get(seller_address)

    if volume == 0:
        state = Request.STATE_FATAL
        message = SellMarketOrderRequest.MSG_ZERO_TOTAL_VOLUME
    elif seller is None:
        state = Request.STATE_FATAL
        message = SellMarketOrderRequest.MSG_USER_DOES_NOT_EXISTS
    elif seller.available < volume:
        state = Request.STATE_FATAL
        message = SellMarketOrderRequest.MSG_AVAILABLE_ASSET_NOT_ENOUGH

    req = SellMarketOrderRequest(transaction, service_address, block_timestamp, volume)

    if state != Request.STATE_OK:
        req.state = state
        req.message = message
        return req
    else:  # start processing limit sell
        #change
        _add_payment(req, {seller_address: sbtc_amount})
        seller.available -= volume

        while True:
            if asset.buy_order_book:  # can sell something
                if asset.buy_order_book[0].volume_unfulfilled >= req.volume_unfulfilled:  # req is fully fulfilled
                    _trade(req, asset.buy_order_book[0])

                    if asset.buy_order_book[0].volume_unfulfilled == 0:  # two orders both fulfilled
                        del asset.users[asset.buy_order_book[0].user_address].active_orders[
                            asset.buy_order_book[0].order_index]
                        del asset.buy_order_book[0]

                    break
                else:  # only the buy order is fully fulfilled
                    _trade(req, asset.buy_order_book[0])
                    del asset.users[asset.buy_order_book[0].user_address].active_orders[
                        asset.buy_order_book[0].order_index]
                    del asset.buy_order_book[0]
            else:  # can not sell anything
                break

        req.state = Request.STATE_OK
        return req


def clear_order(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    index = kwargs['sbtc_amount'] % OneHundredMillion
    req = ClearOrderRequest(transaction, service_address, block_timestamp, index)

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    user = asset.users.get(req.user_address)

    if user is None:
        req.state = Request.STATE_FATAL
        req.message = ClearOrderRequest.MSG_USER_DOES_NOT_EXISTS
        return req
    elif index == 0:
        req.state = Request.STATE_FATAL
        req.message = ClearOrderRequest.MSG_INDEX_IS_ZERO
        return req
    else:  # request is legit, start real execution
        _add_payment(req, kwargs['sbtc_amount'])  # change

        assert isinstance(user, User)
        if index not in user.active_orders:
            req.message = ClearOrderRequest.MSG_ORDER_DOES_NOT_EXIST
        else:
            order = user.active_orders[index]
            order.trade_history.add(TradeItem.trade_cancelled(block_timestamp))
            del user.active_orders[index]

            assert isinstance(order, BuyLimitOrderRequest) or isinstance(order, SellLimitOrderRequest)
            if isinstance(order, BuyLimitOrderRequest):
                asset.buy_order_book.remove(order)
                _add_payment(req, {order.user_address: order.volume_unfulfilled * order.unit_price})
            else:
                asset.sell_order_book.remove(order)
                user.available += order.volume_unfulfilled

        req.state = Request.STATE_OK
        return req


def transfer(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    service_address = kwargs['service_address']
    user_address = transaction.input_addresses[0]

    targets = {}
    for n, transfer_address, transfer_value in transaction.outputs:
        if transfer_address in [service_address, user_address]:
            continue

        amount = transfer_value % OneHundredMillion
        if amount != 0:
            targets[transfer_address] = amount

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    req = TransferRequest(transaction, service_address, block_timestamp, targets)
    total_transfer = sum(targets.values())

    if not targets:
        req.state = Request.STATE_FATAL
        req.message = TransferRequest.MSG_NO_VALID_TARGET
        return req
    elif user_address not in asset.users:
        req.state = Request.STATE_FATAL
        req.message = TransferRequest.MSG_USER_DOES_NOT_EXISTS
        return req
    elif asset.users[user_address].available < total_transfer:
        req.state = Request.STATE_FATAL
        req.message = TransferRequest.MSG_NOT_ENOUGH_ASSET
        return req
    else:  # executable
        for address, amount in targets.iteritems():
            if address not in asset.users:
                asset.users[address] = User()

            asset.users[address].total += amount
            asset.users[address].available += amount

        asset.users[user_address].total -= total_transfer
        asset.users[user_address].available -= total_transfer

        _add_payment(req, {user_address: kwargs['sbtc_amount']})

        req.state = Request.STATE_OK
        return req


def create_vote(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    from datetime import timedelta

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    user_address = transaction.input_addresses[0]
    sbtc_amount = kwargs['sbtc_amount']
    n_days_expiration = sbtc_amount % OneHundredMillion

    #this won't affect any thing in asset, so we don't care whether all these inputs are legit for now
    index = len(asset.votes) + 1

    req = CreateVoteRequest(transaction, service_address, block_timestamp,
                            block_timestamp + timedelta(days=n_days_expiration), index)

    if asset.issuer_address != user_address:
        req.state = Request.STATE_FATAL
        req.message = CreateVoteRequest.MSG_SENDER_IS_NOT_ISSUER
        return req
    elif n_days_expiration == 0:
        req.state = Request.STATE_FATAL
        req.message = CreateVoteRequest.MSG_LAST_ZERO_DAYS
        return req
    else:  # inputs are legit, start processing
        assert index not in asset.votes
        asset.votes[index] = Vote(block_timestamp, req.expire_time, {})
        _add_payment(req, sbtc_amount)


def user_vote(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    sbtc_amount = kwargs['sbtc_amount']
    index = sbtc_amount % 1000
    option = index // 1000

    user_address = transaction.input_addresses[0]

    req = UserVoteRequest(transaction, service_address, block_timestamp, index, option)

    if user_address not in asset.users or asset.users[user_address].total == 0:
        req.state = Request.STATE_FATAL
        req.message = UserVoteRequest.MSG_SENDER_IS_NOT_LEGIT
        return req
    elif index not in asset.votes:
        req.state = Request.STATE_FATAL
        req.message = UserVoteRequest.MSG_VOTE_DOES_NOT_EXIST
        return req
    else:  # all inputs are legit, process the voting
        vote = asset.votes[index]

        #refund
        _add_payment(req, {user_address: sbtc_amount})

        if vote.expire_time <= block_timestamp:
            req.message = UserVoteRequest.MSG_VOTE_CLOSED
        elif index in asset.users[user_address].vote:
            req.message = UserVoteRequest.MSG_ALREADY_VOTED
        else:
            asset.users[user_address].vote[index] = option

            weight = asset.users[user_address].total
            if option in vote.vote_stat:
                vote.vote_stat[option] += weight
            else:
                vote.vote_stat[option] = weight

        req.state = Request.STATE_OK

        return req


def pay(transaction, service_address, block_timestamp, **kwargs):
    """
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    pay_amount = kwargs['sbtc_amount']
    DPS = pay_amount // asset.total_shares
    change = pay_amount - DPS * asset.total_shares

    req = PayRequest(transaction, service_address, block_timestamp, pay_amount, DPS, change)
    assert asset.total_shares == sum([u.total for u in asset.users.values()])

    if asset.issuer_address not in transaction.input_addresses:
        req.state = Request.STATE_FATAL
        req.message = PayRequest.MSG_PAYER_ILLEGIT
        return req

    _add_payment(req, {asset.issuer_address: change})
    _add_payment(req, {address: user.total * DPS for address, user in asset.users.iteritems()})

    req.state = Request.STATE_OK
    return req


def asset_state_control(transaction, service_address, block_timestamp, **kwargs):
    """
    no need to pay back for asset state control requests
    :type transaction: Transaction
    :type service_address: str
    :type block_timestamp: datetime
    :rtype: Request
    """
    exchange = kwargs['exchange']

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    request_state = kwargs['sbtc_amount'] % OneHundredMillion
    req = AssetStateControlRequest(transaction, service_address, block_timestamp, request_state)

    if exchange.open_exchange_address not in transaction.input_addresses:
        req.state = Request.STATE_FATAL
        req.message = AssetStateControlRequest.MSG_INPUT_ADDRESS_NOT_LEGIT
    elif request_state not in [AssetStateControlRequest.STATE_RESUME, AssetStateControlRequest.STATE_PAUSE] \
            and request_state % 10 != 3:
        req.state = Request.STATE_FATAL
        req.message = AssetStateControlRequest.MSG_STATE_NOT_SUPPORTED
    else:
        if request_state == AssetStateControlRequest.STATE_RESUME:
            asset.state = Asset.STATE_RUNNING
            req.state = Request.STATE_OK
        elif request_state == AssetStateControlRequest.STATE_PAUSE:
            asset.state = Asset.STATE_PAUSED
            req.state = Request.STATE_OK
        else:
            assert request_state % 10 == 3
            if asset.state == Asset.STATE_RUNNING:
                req.state = Request.STATE_FATAL
                req.message = AssetStateControlRequest.MSG_CAN_NOT_REINIT_WHEN_RUNNING
            else:
                assert asset.state == Asset.STATE_PAUSED
                asset = kwargs['asset_init_data'][request_state // 10]
                if not (isinstance(asset, Asset) and asset.state == Asset.STATE_PAUSED):
                    raise InitDataError(asset=asset, asset_state=asset.state)

                exchange.assets[kwargs['asset_name']] = asset
                req.state = Request.STATE_OK

    return req