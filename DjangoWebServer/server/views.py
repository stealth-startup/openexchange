from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
import json
from openexchangelib import util
from openexchangelib import types
import functools
from models import ChainedState, UserPayLog, StaticData
import helpers
from decimal import Decimal


logger = util.get_logger('django_server')
write_log = functools.partial(util.write_log, logger)
OneHundredMillionF = 100000000.0

####################custmize some default pages#######
def forbidden_403(request):
    return render_to_response("403.html")


def page_not_found_404(request):
    return render_to_response("404.html")


def server_error_500(request):
    return render_to_response("500.html")


####################pages#####################
def home(request):
    return render_to_response('home.html')


def market(request):
    assets = [
        {
            'name': asset_name,
            'url': '/asset/' + asset_name,
            'img_url': '/static/img/' + asset_name + '.jpg'
        } for asset_name in ChainedState.get_latest_state().exchange.assets
    ]
    asset_rows = [
        assets[i * 3: i * 3 + 3]
        for i in xrange(len(assets) // 3 + 1)
    ]
    return render_to_response('market.html', {'asset_rows': asset_rows})


def account(request, asset_name, user_address):
    def get_html(obj):
        if isinstance(obj, list):
            return "<ul>" + ''.join([get_html(log) for log in obj]) + "</ul>"
        else:
            if isinstance(obj, types.BuyLimitOrderRequest):
                return "<li>%s Limit Buy. Amount=%d Unit Price=%f BTC<ul>%s</ul></li>" % \
                       (
                           helpers.format_time(obj.block_timestamp), obj.volume_requested,
                           obj.unit_price / OneHundredMillionF,
                           get_html(obj.trade_history))
            elif isinstance(obj, types.SellLimitOrderRequest):
                return "<li>%s Limit Sell. Amount=%d Unit Price=%f BTC<ul>%s</ul></li>" % \
                       (
                           helpers.format_time(obj.block_timestamp), obj.volume_requested,
                           obj.unit_price / OneHundredMillionF,
                           get_html(obj.trade_history))
            elif isinstance(obj, types.BuyMarketOrderRequest):
                return "<li>%s Market Buy. Total Value=%f BTC<ul>%s</ul></li>" % \
                       (helpers.format_time(obj.block_timestamp), obj.total_price_requested / OneHundredMillionF,
                        get_html(obj.trade_history))
            elif isinstance(obj, types.SellMarketOrderRequest):
                return "<li>%s Market Sell. Amount=%f <ul>%s</ul></li>" % \
                       (helpers.format_time(obj.block_timestamp), obj.volume_requested,
                        get_html(obj.trade_history))
            elif isinstance(obj, types.TransferRequest):
                return "<li>%s Transfer. Transfer To:<ul>%s</ul></li>" % \
                       (helpers.format_time(obj.block_timestamp),
                        ''.join(
                            ["<li>%s: %d</li>" % (addr, amount) for addr, amount in obj.transfer_targets.iteritems()]))
            elif isinstance(obj, UserPayLog):
                return "<li>%s DPS = %f BTC, share number = %d, payment received = %f BTC</li>" % \
                       (helpers.format_time(obj.block_timestamp), obj.DPS / OneHundredMillionF, obj.share_N,
                        obj.DPS * obj.share_N)
            elif isinstance(obj, types.TradeItem) and obj.trade_type == types.TradeItem.TRADE_TYPE_CANCELLED:
                return "<li>Canceled by user</li>"
            elif isinstance(obj, types.TradeItem) and obj.trade_type != types.TradeItem.TRADE_TYPE_CANCELLED:
                return "<li>%s Trade Amount: %d, Unit Price: %f BTC</li>" % \
                       (helpers.format_time(obj.timestamp), obj.amount, obj.unit_price / OneHundredMillionF)
            else:
                raise NotImplementedError()

    chained_state = ChainedState.get_latest_state()

    try:
        tradings = [t for t in chained_state.user_history[asset_name][user_address]
                    if
                    isinstance(t, (types.BuyLimitOrderRequest, types.SellLimitOrderRequest, types.BuyMarketOrderRequest,
                                   types.SellMarketOrderRequest, types.TransferRequest))]
    except:
        tradings = []
    if tradings:
        trade_html = get_html(tradings)
    else:
        trade_html = "<ul><li>Empty</li></ul>"

    try:
        pays = [t for t in chained_state.user_history[asset_name][user_address] if isinstance(t, UserPayLog)]
    except:
        pays = []
    if pays:
        pay_html = get_html(pays)
    else:
        pay_html = "<ul><li>Empty</li></ul>"

    try:
        failures = [t for t in chained_state.failed_requests if t.transaction.input_address == user_address]
    except:
        failures = []
    if failures:
        failures_html = "<ul>%s</ul>" % (''.join(
            ["<li>%s transaction hash: %s</li>" % (helpers.format_time(o.block_timestamp), o.transaction.hash) for
             o in failures]))
    else:
        failures_html = ""  # we don't display the failure tag, this value is used in the template

    return render_to_response('account.html', {
        'asset_name': asset_name,
        'trade_html': trade_html,
        'pay_html': pay_html,
        'failures_html': failures_html
    })


def help(request):
    return render_to_response('help.html')


def asset(request, asset_name):
    chained_state = ChainedState.get_latest_state()
    if asset_name not in chained_state.exchange.assets:
        raise Http404

    asset = chained_state.exchange.assets[asset_name]
    static_data = StaticData.get_static_data()
    try:
        asset_intro = static_data.asset_descriptions[asset_name]
    except:
        asset_intro = "N/A"

    return render_to_response('asset.html',
                              {
                                  'asset_name': asset_name,
                                  'limit_buy_address': asset.limit_buy_address,
                                  'limit_sell_address': asset.limit_sell_address,
                                  'market_buy_address': asset.market_buy_address,
                                  'market_sell_address': asset.market_sell_address,
                                  'clear_order_address': asset.clear_order_address,
                                  'asset_intro': asset_intro
                              })

#########################apis####################


def chart_data(request, asset_name):
    """
    :type asset_name: str
    """
    return HttpResponse(json.dumps(ChainedState.get_latest_state().chart_data.get(asset_name, [])),
                        mimetype="application/json")


def asset_order_book(request, asset_name):
    return HttpResponse(json.dumps(ChainedState.get_latest_state().order_book.get(asset_name, {'ask': [], 'bid': []})),
                        mimetype="application/json")


def recent_trades(request, asset_name):
    """
    :type asset_name: str
    """
    chained_state = ChainedState.get_latest_state()
    raw_data = chained_state.recent_trades.get(asset_name, [])
    """:type: list of types.TradeItem"""

    data = [
        [
            d.timestamp.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            'Buy' if d.trade_type == types.TradeItem.TRADE_TYPE_BUY else 'Sell',
            str(Decimal(d.unit_price) / 100000000),
            d.amount,
            str(Decimal(d.unit_price) * d.amount / 100000000),
        ] for d in raw_data
    ]
    return HttpResponse(json.dumps(data), mimetype="application/json")


def recent_requests(request, asset_name):
    """
    :type asset_name: str
    """
    chained_state = ChainedState.get_latest_state()
    raw_data = chained_state.recent_requests.get(asset_name, [])
    """:type: list of types.Request"""

    data = [
        [
            d.block_timestamp.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
            '<a href="http://blockchain.info/tx/%s" target="_blank">%s</a>' % (d.transaction.hash, d.transaction.hash[:20]+'...'),
            '<a href="http://blockchain.info/address//%s" target="_blank>%s</a>' % (d.transaction.input_addresses[0], d.transaction.input_addresses[0]),
            '<span class="label label-success">OK</span>' if d.state == types.Request.STATE_OK else '<span class="label label-important">Error</span>',
        ] for d in raw_data
    ]
    return HttpResponse(json.dumps(data), mimetype="application/json")


def asset_page_login(request, asset_name, user_address):
    """
    :type asset_name: str
    :type user_address: str
    """
    assets = ChainedState.get_latest_state().exchange.assets
    default_data = {
        'balance': 'Total:0, Available:0, Freeze:0',
        'active_orders': []
    }

    if asset_name not in assets:
        data = default_data
    elif user_address not in assets[asset_name].users:
        data = default_data
    else:
        user = assets[asset_name].users[user_address]
        data = {
            'balance': 'Total:%d Available:%d In Order Book:%d' % (user.total, user.available, user.total - user.available),
            'active_orders': [[
                                  order.block_timestamp.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),  # time
                                  'Buy' if isinstance(order, types.BuyLimitOrderRequest) else 'Sell',  # type
                                  str(Decimal(order.unit_price) / 100000000),  # unit_price
                                  order.volume_unfulfilled,  # amount
                                  str(Decimal(order.volume_unfulfilled) * order.unit_price / 100000000),  # total btc
                                  idx  # index
                              ] for idx, order in user.active_orders.iteritems()]
        }
    return HttpResponse(json.dumps(data), mimetype="application/json")


def auth(request):
    type = request.GET.get('type', 'login')
    assert type in ['login', 'logout']

    address = request.GET.get('address')  # TODO check user_address format (optional)

    if type == 'login' and (address or request.session.get('address')):
        if address:
            request.session['address'] = address
        address = request.session.get('address')

        return HttpResponse(json.dumps({
            'address': address,
            'assets': [
                {
                    'asset_name': asset_name,
                    'asset_transfer_address': asset.transfer_address,
                    'total': asset.users[address].total,
                    'available': asset.users[address].available,
                } for asset_name, asset in ChainedState.get_latest_state().exchange.assets.iteritems() if
                address in asset.users
            ]}), mimetype="application/json")
    else:
        for key in request.session.keys():
            del request.session[key]
        return HttpResponse(json.dumps(None), mimetype="application/json")

