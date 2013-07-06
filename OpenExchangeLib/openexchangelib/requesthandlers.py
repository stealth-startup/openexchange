from types import *

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

        if address in request.related_payments:
            request.related_payments[address] += amount
        else:
            request.related_payments[address] = amount


def _place_buy_limit_order(buy_order_book, buy_order):
    """
    since we execute the requests in the order of their transactions, so we don't need timestamp for sorting.
    in fact, their incoming order is more trustworthy than their timestamp since timestamp could be manipulated
    the buy_order_book is sorted in descending order by unit price; if two requests have the same unit price, the new
    one should be the latter
    TODO: can improve time efficiency by binary search
    :type buy_order_book: list of BuyLimitOrder
    :type buy_order: BuyLimitOrder
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
    :type sell_order_book: list of SellLimitOrder
    :type sell_order: SellLimitOrder
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


def _trade_general(buy_request, sell_request, buyer, seller, unit_price, volume, timestamp):
    """
    manipulate asset record and trade history for users. will not touch anything with payments
    :type buy_request: BuyLimitOrder or BuyMarketOrder
    :type sell_request: SellLimitOrder or SellMarketOrder
    :type buyer: User
    :type seller: User
    :type unit_price: int
    :type volume: int
    :type timestamp: datetime
    """
    assert buyer.available >= 0
    assert buyer.total >= 0
    assert seller.total - seller.available >= volume
    assert seller.available >= 0

    if isinstance(buy_request, BuyLimitOrder):
        buy_request.volume_unfulfilled -= volume
    else:
        assert isinstance(buy_request, BuyMarketOrder)
        buy_request.total_price_unfulfilled -= unit_price * volume
        buy_request.volume_fulfilled += volume

    if isinstance(sell_request, SellLimitOrder):
        sell_request.volume_unfulfilled -= volume
    else:
        assert isinstance(sell_request, SellMarketOrder)
        sell_request.volume_unfulfilled -= volume
        sell_request.price_total_sold += unit_price * volume

    buy_request.trade_history.append(TradeItem(unit_price, volume, timestamp, 'buy'))
    sell_request.trade_history.append(TradeItem(unit_price, volume, timestamp, 'sell'))

    buyer.available += volume
    buyer.total += volume

    seller.total -= volume


################################### handlers
def create_asset(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """
    exchange = kwargs['exchange']
    sbtc_amount = kwargs['sbtc_amount']
    n = sbtc_amount % OneHundredMillion
    req = CreateAsset(transaction, block_timestamp, n)

    if transaction.input_address != exchange.open_exchange_address:
        req.state = Request.STATE_FATAL
        req.message = CreateAsset.MSG_INPUT_ADDRESS_NOT_LEGIT
    else:
        asset_name, new_asset = kwargs['asset_init_data'][n]
        assert isinstance(asset_name, str)
        assert isinstance(new_asset, Asset)

        if asset_name in exchange.assets:
            req.state = Request.STATE_FATAL
            req.message = CreateAsset.MSG_ASSET_ALREADY_REGISTERED
        else:
            req.state = Request.STATE_OK
            exchange.assets[asset_name] = new_asset

    return req


def exchange_state_control(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """
    exchange = kwargs['exchange']
    state = kwargs['sbtc_amount'] % OneHundredMillion
    req = ExchangeStateControl(transaction, block_timestamp, state)

    if transaction.input_address != exchange.open_exchange_address:
        req.state = Request.STATE_FATAL
        req.message = ExchangeStateControl.MSG_INPUT_ADDRESS_NOT_LEGIT
    elif state not in [1, 2]:
        req.state = Request.STATE_FATAL
        req.message = ExchangeStateControl.MSG_STATE_NOT_SUPPORTED
    else:
        if state == ExchangeStateControl.STATE_RESUME:
            exchange.state = Exchange.STATE_RUNNING
        else:
            assert state == ExchangeStateControl.STATE_PAUSE
            exchange.state = Exchange.STATE_PAUSED

        req.state = Request.STATE_OK

    return req


def limit_buy(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, volume, sell_order):
        """
        :type req: BuyLimitOrder
        :type volume: int
        :type sell_order: SellLimitOrder
        """
        unit_price = sell_order.unit_price
        assert isinstance(unit_price, int)
        asset = kwargs['asset']

        buyer = asset.users.get(req.user_address)
        assert isinstance(buyer, User)

        seller = asset.users.get(sell_order.user_address)
        assert isinstance(seller, User)

        _trade_general(req, sell_order, buyer, seller, unit_price, volume, block_timestamp)

        #refund to buyer
        _add_payment(req, {req.user_address: (req.unit_price - unit_price) * volume})
        #withdraw to seller
        _add_payment(req, {sell_order.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #buyer_address
    buyer_address = transaction.input_address

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
        message = BuyLimitOrder.MSG_ZERO_VOLUME
    elif unit_price * volume != sbtc_amount - volume or unit_price < 10000 or unit_price % 10000 != 0:
        state = Request.STATE_FATAL
        message = BuyLimitOrder.MSG_UNIT_PRICE_ILLEGIT

    #buyer and order index
    if buyer_address not in asset.users:
        asset.users[buyer_address] = User()
    buyer = asset.users[buyer_address]

    if state == Request.STATE_OK:
        buyer.order_counter += 1
        order_index = buyer.order_counter
    else:
        order_index = None

    req = BuyLimitOrder(transaction, block_timestamp, buyer_address, order_index, volume, unit_price)

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

        req.state = BuyLimitOrder.STATE_OK
        return req


def limit_sell(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, volume, buy_order):
        """
        :type req: SellLimitOrder
        :type volume: int
        :type buy_order: BuyLimitOrder
        """
        unit_price = buy_order.unit_price
        assert isinstance(unit_price, int)
        asset = kwargs['asset']

        seller = asset.users.get(req.user_address)
        assert isinstance(seller, User)

        buyer = asset.users.get(buy_order.user_address)
        assert isinstance(buyer, User)

        _trade_general(buy_order, req, buyer, seller, unit_price, volume, block_timestamp)

        #withdraw to seller
        _add_payment(req, {req.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #seller_address
    seller_address = transaction.input_address

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
        message = SellLimitOrder.MSG_ZERO_VOLUME
    elif unit_price == 0:
        state = Request.STATE_FATAL
        message = SellLimitOrder.MSG_UNIT_PRICE_ILLEGIT
    elif seller is None:
        state = Request.STATE_FATAL
        message = SellLimitOrder.MSG_USER_DOES_NOT_EXISTS
    elif seller.available < volume:
        state = Request.STATE_FATAL
        message = SellLimitOrder.MSG_NOT_ENOUGH_ASSET

    if state == Request.STATE_OK:
        seller.order_counter += 1
        order_index = seller.order_counter
    else:
        order_index = None

    req = SellLimitOrder(transaction, block_timestamp, seller_address, order_index, volume, unit_price)

    if state != Request.STATE_OK:
        req.state = state
        req.message = message
        return req
    else:  # start processing limit sell
        seller.active_orders[order_index] = req

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


def market_buy(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, sell_order):
        """
        :type req: BuyMarketOrder
        :type sell_order: SellLimitOrder
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

        _trade_general(req, sell_order, buyer, seller, unit_price, volume, block_timestamp)

        #withdraw to seller
        _add_payment(req, {sell_order.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #buyer_address
    buyer_address = transaction.input_address

    #unit_price
    total_price = kwargs['sbtc_amount']

    #state and message
    state = Request.STATE_OK
    message = None

    if total_price == 0:  # this should never trigger
        state = Request.STATE_FATAL
        message = BuyMarketOrder.MSG_ZERO_TOTAL_PRICE

    #user and order index
    if buyer_address not in asset.users:
        asset.users[buyer_address] = User()

    req = BuyMarketOrder(transaction, block_timestamp, buyer_address, total_price)

    if state != Request.STATE_OK:
        req.state = state
        req.message = message
        return req
    else:  # start processing limit buy
        while True:
            if asset.sell_order_book and asset.sell_order_book[0].unit_price <= req.total_price_unfulfilled:  # can buy something
                if asset.sell_order_book[0].volume_unfulfilled * asset.sell_order_book[0].unit_price >= req.total_price_unfulfilled:  # req is fully fulfilled
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

        req.state = BuyLimitOrder.STATE_OK
        return req


def market_sell(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """

    def _trade(req, buy_order):
        """
        :type req: SellMarketOrder
        :type buy_order: BuyLimitOrder
        """
        unit_price = buy_order.unit_price
        assert isinstance(unit_price, int)
        asset = kwargs['asset']

        seller = asset.users.get(req.user_address)
        assert isinstance(seller, User)

        buyer = asset.users.get(buy_order.user_address)
        assert isinstance(buyer, User)

        volume = min(buy_order.volume_unfulfilled, req.volume_unfulfilled)

        _trade_general(buy_order, req, buyer, seller, unit_price, volume, block_timestamp)

        #withdraw to seller
        _add_payment(req, {req.user_address: unit_price * volume})

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    #seller_address
    seller_address = transaction.input_address

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
        message = SellMarketOrder.MSG_ZERO_TOTAL_VOLUME
    elif seller is None:
        state = Request.STATE_FATAL
        message = SellMarketOrder.MSG_USER_DOES_NOT_EXISTS
    elif seller.available < volume:
        state = Request.STATE_FATAL
        message = SellMarketOrder.MSG_AVAILABLE_ASSET_NOT_ENOUGH

    req = SellMarketOrder(transaction, block_timestamp, seller_address, volume)

    if state != Request.STATE_OK:
        req.state = state
        req.message = message
        return req
    else:  # start processing limit sell
        #change
        _add_payment(req, {seller_address: sbtc_amount})

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


def clear_order(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """
    index = kwargs['sbtc_amount'] % OneHundredMillion
    req = ClearOrder(transaction, block_timestamp, transaction.input_address, index)

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    user = asset.users.get(req.user_address)

    if user is None:
        req.state = Request.STATE_FATAL
        req.message = ClearOrder.MSG_USER_DOES_NOT_EXISTS
        return req
    elif index == 0:
        req.state = Request.STATE_FATAL
        req.message = ClearOrder.MSG_INDEX_IS_ZERO
        return req
    else:  # request is legit, start real execution
        _add_payment(req, kwargs['sbtc_amount'])  # change

        assert isinstance(user, User)
        if index not in user.active_orders:
            req.state = Request.STATE_NOT_AS_EXPECTED
            req.message = ClearOrder.MSG_ORDER_DOES_NOT_EXIST
            return req
        else:
            order = user.active_orders[index]
            order.trade_history.add(CanceledTrade(block_timestamp))
            del user.active_orders[index]

            assert isinstance(order, BuyLimitOrder) or isinstance(order, SellLimitOrder)
            if isinstance(order, BuyLimitOrder):
                asset.buy_order_book.remove(order)
                _add_payment(req, {order.user_address: order.volume_unfulfilled * order.unit_price})
            else:
                asset.sell_order_book.remove(order)
                user.available += order.volume_unfulfilled

            req.state = Request.STATE_OK
            return req


def transfer(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """

    service_address = kwargs['service_address']
    user_address = transaction.input_address

    targets = {}
    for transfer_address, transfer_value in transaction.outputs.iteritems():
        if transfer_address in [service_address, user_address]:
            continue

        amount = transfer_value % OneHundredMillion
        if amount != 0:
            targets[transfer_address] = amount

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    req = Transfer(transaction, block_timestamp, targets)
    total_transfer = sum(targets.values())

    if not targets:
        req.state = Request.STATE_FATAL
        req.message = Transfer.MSG_NO_VALID_TARGET
        return req
    elif user_address not in asset.users:
        req.state = Request.STATE_FATAL
        req.message = Transfer.MSG_USER_DOES_NOT_EXISTS
        return req
    elif asset.users[user_address].available < total_transfer:
        req.state = Request.STATE_FATAL
        req.message = Transfer.MSG_NOT_ENOUGH_ASSET
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


def create_vote(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """
    from datetime import timedelta

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    user_address = transaction.input_address
    sbtc_amount = kwargs['sbtc_amount']
    n_days_expiration = sbtc_amount % OneHundredMillion

    #this won't affect any thing in asset, so we don't care whether all these inputs are legit for now
    index = len(asset.votes) + 1

    req = CreateVote(transaction, block_timestamp, block_timestamp + timedelta(days=n_days_expiration), index)

    if asset.issuer_address != user_address:
        req.state = Request.STATE_FATAL
        req.message = CreateVote.MSG_SENDER_IS_NOT_ISSUER
        return req
    elif n_days_expiration == 0:
        req.state = Request.STATE_FATAL
        req.message = CreateVote.MSG_LAST_ZERO_DAYS
        return req
    else:  # inputs are legit, start processing
        assert index not in asset.votes
        asset.votes[index] = Vote(block_timestamp, req.expire_time, {})
        _add_payment(req, sbtc_amount)


def vote(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """
    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    sbtc_amount = kwargs['sbtc_amount']
    index = sbtc_amount % 1000
    option = index // 1000

    user_address = transaction.input_address

    req = VoteRequest(transaction, block_timestamp, index, option)

    if user_address not in asset.users or asset.users[user_address].total == 0:
        req.state = Request.STATE_FATAL
        req.message = VoteRequest.MSG_SENDER_IS_NOT_LEGIT
        return req
    elif index not in asset.votes:
        req.state = Request.STATE_FATAL
        req.message = VoteRequest.MSG_VOTE_DOES_NOT_EXIST
        return req
    else:  # all inputs are legit, process the voting
        vote = asset.votes[index]

        #refund
        _add_payment(req, {user_address: sbtc_amount})

        if vote.expire_time <= block_timestamp:
            req.state = Request.STATE_NOT_AS_EXPECTED
            req.message = VoteRequest.MSG_VOTE_CLOSED
        elif index in asset.users[user_address].vote:
            req.state = Request.STATE_NOT_AS_EXPECTED
            req.message = VoteRequest.MSG_ALREADY_VOTED
        else:
            asset.users[user_address].vote[index] = option

            weight = asset.users[user_address].total
            if option in vote.vote_stat:
                vote.vote_stat[option] += weight
            else:
                vote.vote_stat[option] = weight

            req.state = Request.STATE_OK

        return req


def pay(transaction, block_timestamp, **kwargs):
    """
    :type transaction: SITransaction
    :type block_timestamp: datetime
    :rtype: Request
    """
    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    payer = transaction.input_address
    pay_amount = kwargs['sbtc_amount']

    DPS = pay_amount // asset.total_shares
    change = pay_amount - DPS * asset.total_shares

    req = Pay(transaction, block_timestamp, payer, pay_amount, DPS, change)
    assert asset.total_shares == sum([u.total for u in asset.users.values()])

    _add_payment(req, {payer: change})
    _add_payment(req, {address: user.total * DPS for address, user in asset.users.iteritems()})

    req.state = Request.STATE_OK
    return req


def asset_state_control(transaction, block_timestamp, **kwargs):
    """
    no need to pay back for asset state control requests
    :type block_timestamp: datetime
    :type transaction: SITransaction
    :rtype: Request
    """
    exchange = kwargs['exchange']

    asset = kwargs['asset']
    assert isinstance(asset, Asset)

    state = kwargs['sbtc_amount'] % OneHundredMillion
    req = ExchangeStateControl(transaction, block_timestamp, state)

    if transaction.input_address != exchange.open_exchange_address:
        req.state = Request.STATE_FATAL
        req.message = AssetStateControl.MSG_INPUT_ADDRESS_NOT_LEGIT
    elif state not in [AssetStateControl.STATE_RESUME, AssetStateControl.STATE_PAUSE] or state % 10 != 3:
        req.state = Request.STATE_FATAL
        req.message = AssetStateControl.MSG_STATE_NOT_SUPPORTED
    else:
        if state == AssetStateControl.STATE_RESUME:
            asset.state = Asset.STATE_RUNNING
        elif state == AssetStateControl.STATE_PAUSE:
            asset.state = Asset.STATE_PAUSED
        else:
            assert state % 10 == 3
            if asset.state == Asset.STATE_RUNNING:
                #in this case, we just ignore this request, because we cannot update the asset when it's running
                req.state = Request.STATE_NOT_AS_EXPECTED
                req.message = AssetStateControl.MSG_CAN_NOT_REINIT_WHEN_RUNNING
            else:
                assert asset.state == Asset.STATE_PAUSED
                exchange.assets[kwargs['asset_name']] = kwargs['asset_init_data'][state // 10]
                req.state = Request.STATE_OK

    return req