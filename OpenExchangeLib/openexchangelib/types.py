####################  Exceptions
import settings
from pybit.types import Transaction, Printable


class OEBaseException(Exception):
    def __init__(self, *args, **kwargs):
        lkw = ["%s: %s" % (str(k), str(v)) for k, v in kwargs]
        Exception.__init__(self, *(args + tuple(lkw)))


class Request(Printable):  # base class for all requests
    STATE_NOT_PROCESSED = 0
    STATE_OK = 1
    STATE_FATAL = 2

    MSG_STATE_NOT_AS_EXPECTED = 1000
    MSG_IGNORED_SINCE_EXCHANGE_PAUSED = 1001
    MSG_IGNORED_SINCE_ASSET_PAUSED = 1002

    def __init__(self, transaction, service_address, block_timestamp):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        """
        self.transaction = transaction
        self.service_address = service_address
        self.block_timestamp = block_timestamp

        self.state = self.__class__.STATE_NOT_PROCESSED
        self.message = None
        self.related_payments = {}

    @classmethod
    def ignored_request(cls, transaction, service_address, block_timestamp, msg):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type msg: int
        """
        req = cls(transaction, service_address, block_timestamp)
        req.state = cls.STATE_FATAL
        req.message = msg
        return req


class CreateAssetRequest(Request):
    # message ids starts from 10000
    MSG_ASSET_ALREADY_REGISTERED = 10000
    MSG_INPUT_ADDRESS_NOT_LEGIT = 10001

    def __init__(self, transaction, service_address, block_timestamp, file_id):
        """
        :type transaction: Transaction
        :type block_timestamp: datetime
        :type service_address: str
        :type file_id: int
        """
        super(CreateAssetRequest, self).__init__(transaction, service_address, block_timestamp)
        self.file_id = file_id


class ExchangeStateControlRequest(Request):
    STATE_RESUME = 1  # request state, this will not conflict with Request.STATE_XX since they are in different use
    STATE_PAUSE = 2

    # message ids starts from 10000
    MSG_STATE_NOT_SUPPORTED = 10000
    MSG_INPUT_ADDRESS_NOT_LEGIT = 10001

    def __init__(self, transaction, service_address, block_timestamp, request_state):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type request_state: int
        """
        super(ExchangeStateControlRequest, self).__init__(transaction, service_address, block_timestamp)
        self.request_state = request_state


class TradeItem(Printable):
    TRADE_TYPE_BUY = 1
    TRADE_TYPE_SELL = 2
    TRADE_TYPE_CANCELLED = 3

    def __init__(self, unit_price, amount, timestamp, trade_type):
        """
        :type unit_price: int
        :type amount: int
        :type timestamp: datetime
        :type trade_type: int
        """
        self.unit_price = unit_price
        self.amount = amount
        self.timestamp = timestamp
        self.trade_type = trade_type

    @classmethod
    def trade_cancelled(cls, timestamp):
        """
        :type timestamp: datetime
        """
        return cls(None, None, timestamp, cls.TRADE_TYPE_CANCELLED)


class BuyLimitOrderRequest(Request):
    # message ids starts from 10000
    MSG_ZERO_VOLUME = 10000
    MSG_UNIT_PRICE_ILLEGIT = 10001

    def __init__(self, transaction, service_address, block_timestamp, order_index, volume, unit_price):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :param order_index: every order of a user has a unique index
        :type order_index: int or None
        :type volume: int
        :type unit_price: int or None
        """
        super(BuyLimitOrderRequest, self).__init__(transaction, service_address, block_timestamp)

        self.user_address = transaction.input_addresses[0]
        self.order_index = order_index
        self.volume_requested = volume
        self.volume_unfulfilled = volume
        self.unit_price = unit_price

        self.trade_history = []
        """:type: list of TradeItem"""
        self.immediate_executed_trades = []  # this field is for recent-trades and chart-data
        """:type: list of TradeItem"""


class SellLimitOrderRequest(Request):
    # message ids starts from 10000
    MSG_ZERO_VOLUME = 10000
    MSG_UNIT_PRICE_ILLEGIT = 10001
    MSG_USER_DOES_NOT_EXISTS = 1002
    MSG_NOT_ENOUGH_ASSET = 1003

    def __init__(self, transaction, service_address, block_timestamp, order_index, volume, unit_price):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :param order_index: every order of a user has a unique index
        :type order_index: int or None
        :type volume: int
        :type unit_price: int or None
        """
        super(SellLimitOrderRequest, self).__init__(transaction, service_address, block_timestamp)

        self.user_address = transaction.input_addresses[0]
        self.order_index = order_index
        self.volume_requested = volume
        self.volume_unfulfilled = volume
        self.unit_price = unit_price

        self.trade_history = []
        """:type: list of TradeItem"""
        self.immediate_executed_trades = []  # this field is for recent-trades and chart-data
        """:type: list of TradeItem"""


class BuyMarketOrderRequest(Request):
    # message ids starts from 10000
    MSG_ZERO_TOTAL_PRICE = 10000

    def __init__(self, transaction, service_address, block_timestamp, total_price):
        """
        buy market order won't have order index since it will be executed immediately, it's not possible to cancel
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :param total_price: total money for buying at market, will try to spend them all.(amount is always integer)
        :type total_price: int
        """
        super(BuyMarketOrderRequest, self).__init__(transaction, service_address, block_timestamp)

        self.user_address = transaction.input_addresses[0]
        self.total_price_requested = total_price

        self.total_price_unfulfilled = total_price
        self.volume_fulfilled = 0

        self.trade_history = []
        """:type: list of TradeItem"""


class SellMarketOrderRequest(Request):
    # message ids starts from 10000
    MSG_ZERO_TOTAL_VOLUME = 10000
    MSG_USER_DOES_NOT_EXISTS = 10001
    MSG_AVAILABLE_ASSET_NOT_ENOUGH = 10002

    def __init__(self, transaction, service_address, block_timestamp, volume):
        """
        sell market order won't have order index since it will be executed immediately, not possible to cancel
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type volume: int
        """
        super(SellMarketOrderRequest, self).__init__(transaction, service_address, block_timestamp)
        self.user_address = transaction.input_addresses[0]
        self.volume_requested = volume

        self.volume_unfulfilled = volume
        self.price_total_sold = 0  # money total sold, not volume

        self.trade_history = []
        """:type: list of TradeItem"""


class ClearOrderRequest(Request):
    # message ids starts from 10000
    MSG_USER_DOES_NOT_EXISTS = 10000
    MSG_INDEX_IS_ZERO = 10001
    MSG_ORDER_DOES_NOT_EXIST = 10002

    def __init__(self, transaction, service_address, block_timestamp, index):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type index: int
        """
        super(ClearOrderRequest, self).__init__(transaction, service_address, block_timestamp)
        self.user_address = transaction.input_addresses[0]
        self.index = index


class TransferRequest(Request):
    # message ids starts from 10000
    MSG_USER_DOES_NOT_EXISTS = 10000
    MSG_NO_VALID_TARGET = 10001
    MSG_NOT_ENOUGH_ASSET = 10002

    def __init__(self, transaction, service_address, block_timestamp, transfer_targets):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type transfer_targets: dict from str to int
        """
        super(TransferRequest, self).__init__(transaction, service_address, block_timestamp)

        self.transfer_from = transaction.input_addresses[0]
        self.transfer_targets = transfer_targets


class CreateVoteRequest(Request):
    # message ids starts from 10000
    MSG_SENDER_IS_NOT_ISSUER = 10000
    MSG_LAST_ZERO_DAYS = 10001
    MSG_NOT_ENOUGH_ASSET = 10002

    def __init__(self, transaction, service_address, block_timestamp, expire_time, index):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type expire_time: datetime
        :type index: int
        """
        super(CreateVoteRequest, self).__init__(transaction, service_address, block_timestamp)

        self.expire_time = expire_time
        self.index = index


class UserVoteRequest(Request):
    """
    the name UserVoteRequest is to distinguish with the Vote class in Asset
    """
    # message ids starts from 10000
    MSG_SENDER_IS_NOT_LEGIT = 10000
    MSG_VOTE_CLOSED = 10001
    MSG_ALREADY_VOTED = 10002
    MSG_VOTE_DOES_NOT_EXIST = 10003

    def __init__(self, transaction, service_address, block_timestamp, index, option):
        """
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type index: int
        :type option: int
        """
        super(UserVoteRequest, self).__init__(transaction, service_address, block_timestamp)

        self.index = index
        self.option = option


class PayRequest(Request):

    MSG_PAYER_ILLEGIT = 10000

    def __init__(self, transaction, service_address, block_timestamp, pay_amount, DPS, change):
        """
        :type transaction: Transaction
        :type service_addresss: str
        :type block_timestamp: datetime
        :type pay_amount: int
        :type DPS: int
        :param DPS: dividend per share
        """
        super(PayRequest, self).__init__(transaction, service_address, block_timestamp)

        self.pay_amount = pay_amount
        self.DPS = DPS
        self.change = change


class AssetStateControlRequest(Request):
    STATE_RESUME = 1  # request state, this will not conflict with Request.STATE_XX since they are in different use
    STATE_PAUSE = 2

    # message ids starts from 10000
    MSG_STATE_NOT_SUPPORTED = 10000
    MSG_INPUT_ADDRESS_NOT_LEGIT = 10001
    MSG_CAN_NOT_REINIT_WHEN_RUNNING = 10002

    def __init__(self, transaction, service_address, block_timestamp, request_state):
        """
        since the state could be changed in the later, now we only record the whole state
        detailed analysis could be extend easily by users of this library
        :type transaction: Transaction
        :type service_address: str
        :type block_timestamp: datetime
        :type request_state: int
        """
        super(AssetStateControlRequest, self).__init__(transaction, service_address, block_timestamp)
        self.request_state = request_state


class User(Printable):
    """
    user of a specific asset
    in the Exchange, all assets are in a dict from AssetName -> Asset
    in an Asset, all users are organized by a dict from address -> User
    no history management
    """

    def __init__(self, initial_asset=0):
        """
        :type initial_asset: int
        """
        self.available = initial_asset
        self.total = initial_asset  # total - available == freeze (the once in order book)
        self.vote = {}  # vote index -> vote_value
        self.order_counter = 0
        self.active_orders = {}  # order_id -> order


class Vote(Printable):
    def __init__(self, start_time, expire_time, vote_stat):
        """
        :type start_time: datetime
        :type expire_time: datetime
        :type vote_stat: dict from int to int
        :param vote_stat: votes statistics from options to weight
        """
        self.start_time = start_time
        self.expire_time = expire_time
        self.vote_stat = vote_stat


class Asset(Printable):
    STATE_RUNNING = 1
    STATE_PAUSED = 2

    def __init__(self, total_shares,
                 limit_buy_address, limit_sell_address, market_buy_address, market_sell_address, clear_order_address,
                 transfer_address, pay_address, create_vote_address, vote_address, state_control_address,
                 issuer_address, **kwargs):
        """
        :type total_shares: int
        :type limit_buy_address: str
        :type limit_sell_address: str
        :type market_buy_address: str
        :type market_sell_address: str
        :type clear_order_address: str
        :type transfer_address: str
        :type pay_address: str
        :type create_vote_address: str
        :type vote_address: str
        :type state_control_address: str
        :type issuer_address: str
        """
        self.total_shares = total_shares

        self.limit_buy_address = limit_buy_address
        self.limit_sell_address = limit_sell_address
        self.market_buy_address = market_buy_address
        self.market_sell_address = market_sell_address
        self.clear_order_address = clear_order_address
        self.transfer_address = transfer_address
        self.pay_address = pay_address
        self.create_vote_address = create_vote_address
        self.vote_address = vote_address
        self.state_control_address = state_control_address
        self.issuer_address = issuer_address

        self.sell_order_book = kwargs.get('sell_order_book', [])  # only store ask limit orders, market order will be executed immediately
        """:type: list of SellLimitOrderRequest"""
        self.buy_order_book = kwargs.get('buy_order_book', [])  # only store bid limit orders, market order will be executed immediately
        """:type: list of BuyLimitOrderRequest"""

        self.state = self.__class__.STATE_PAUSED

        self.users = kwargs.get('users', {})
        """:type: dict from str to User"""
        self.votes = kwargs.get('votes', {})  # from vote_id to Vote
        """:type: dict from int to Vote"""


class Exchange(Printable):
    STATE_RUNNING = 0
    STATE_PAUSED = 1

    def __init__(self,
                 processed_block_height=settings.EXCHANGE_INIT_BLOCK_HEIGHT,
                 processed_block_hash=settings.EXCHANGE_INIT_BLOCK_HASH,
                 state_control_address=settings.EXCHANGE_STATE_CONTROL_ADDRESS,
                 create_asset_address=settings.EXCHANGE_CREATE_ASSET_ADDRESS,
                 open_exchange_address=settings.EXCHANGE_OPEN_EXCHANGE_ADDRESS,
                 payment_log_address=settings.EXCHANGE_PAYMENT_LOG_ADDRESS,
                 **kwargs):
        """
        :type processed_block_height: int
        :type processed_block_hash: str
        :type state_control_address: str
        :type create_asset_address: str
        :type open_exchange_address: str
        :type payment_log_address: str
        """
        self.processed_block_height = processed_block_height
        self.processed_block_hash = processed_block_hash

        self.state_control_address = state_control_address
        self.create_asset_address = create_asset_address
        self.open_exchange_address = open_exchange_address
        self.payment_log_address = payment_log_address

        self.assets = kwargs.get('assets', {})
        """:type: dict from str to Asset"""
        self.state = self.__class__.STATE_PAUSED
