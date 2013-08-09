def exchange0():
    """
    :rtype: Exchange
    :return: initial state of OpenExchange
    """
    from openexchangelib.types import Exchange
    return Exchange()


def address_book(exchange):
    """
    :type exchange: OpenExchange
    :rtype: dict
    """
    from openexchangelib import requesthandlers as handlers
    from openexchangelib import types

    service_dict = {
        exchange.create_asset_address: (None, None, handlers.create_asset),
        exchange.state_control_address: (None, None, handlers.exchange_state_control)
    }

    for asset_name, asset in exchange.assets.iteritems():
        assert isinstance(asset_name, str)
        assert isinstance(asset, types.Asset)

        assert asset.limit_buy_address not in service_dict
        service_dict[asset.limit_buy_address] = (asset_name, asset, handlers.limit_buy)

        assert asset.limit_sell_address not in service_dict
        service_dict[asset.limit_sell_address] = (asset_name, asset, handlers.limit_sell)

        assert asset.market_buy_address not in service_dict
        service_dict[asset.market_buy_address] = (asset_name, asset, handlers.market_buy)

        assert asset.market_sell_address not in service_dict
        service_dict[asset.market_sell_address] = (asset_name, asset, handlers.market_sell)

        assert asset.clear_order_address not in service_dict
        service_dict[asset.clear_order_address] = (asset_name, asset, handlers.clear_order)

        assert asset.transfer_address not in service_dict
        service_dict[asset.transfer_address] = (asset_name, asset, handlers.transfer)

        assert asset.create_vote_address not in service_dict
        service_dict[asset.create_vote_address] = (asset_name, asset, handlers.create_vote)

        assert asset.vote_address not in service_dict
        service_dict[asset.vote_address] = (asset_name, asset, handlers.user_vote)

        assert asset.pay_address not in service_dict
        service_dict[asset.pay_address] = (asset_name, asset, handlers.pay)

        assert asset.state_control_address not in service_dict
        service_dict[asset.state_control_address] = (asset_name, asset, handlers.asset_state_control)

    return service_dict


def process_block(exchange, block, asset_init_data=None):
    """
    be aware that the exchange object is changed in-place, and this should be run in a stand-clone process for efficiency
    also no history management is involved for memory efficiency, but one can implement that for their use with ease
    :param exchange: current exchange state
    :type exchange: OpenExchange
    :param block:  next block
    :type block: Block
    :type asset_init_data: dict
    :param asset_init_data: the content depend on whether it's on asset creation or asset re-initialization
    :return: list of processed requests
    :rtype: list of Request
    """
    from openexchangelib import types
    from pybit.types import Block
    from openexchangelib import requesthandlers as handlers

    #make some basic check
    assert exchange.processed_block_height == block.height - 1
    assert exchange.processed_block_hash == block.previous_hash

    service_dict = address_book(exchange)

    # then process the transactions one by one
    requests = []

    assert isinstance(block, Block)
    for tx in block.transactions:
        if exchange.open_exchange_address in tx.input_addresses:
            continue

        for n, address, sbtc_amount in tx.outputs:  # a transaction can have multiple purposes
            if address in service_dict:
                asset_name, asset, handler = service_dict[address]
                assert isinstance(asset_name, str) or asset_name is None
                assert isinstance(asset, types.Asset) or asset is None

                if exchange.state == types.Exchange.STATE_PAUSED:
                    #in this case, only exchange state control order is accepted
                    if address == exchange.state_control_address:
                        req = handler(tx, address, block.timestamp, exchange=exchange, sbtc_amount=sbtc_amount)
                    else:
                        req = types.Request.ignored_request(tx, address, block.timestamp,
                                                            types.Request.MSG_IGNORED_SINCE_EXCHANGE_PAUSED)
                elif asset is not None and asset.state == types.Asset.STATE_PAUSED:
                    if address == asset.state_control_address:
                        req = handler(tx, address, block.timestamp, exchange=exchange, asset=asset,
                                      asset_name=asset_name, sbtc_amount=sbtc_amount, asset_init_data=asset_init_data)
                    else:
                        req = types.Request.ignored_request(tx, address, block.timestamp,
                                                            types.Request.MSG_IGNORED_SINCE_ASSET_PAUSED)
                else:
                    req = handler(tx, address, block.timestamp, exchange=exchange, asset_name=asset_name, asset=asset,
                                  asset_init_data=asset_init_data, sbtc_amount=sbtc_amount)

                requests.append(req)
                #rebuild service_dict when needed
                if handler == handlers.asset_state_control or handler == handlers.create_asset:
                    service_dict = address_book(exchange)

    # other updates
    exchange.processed_block_height = block.height
    exchange.processed_block_hash = block.hash

    return requests
