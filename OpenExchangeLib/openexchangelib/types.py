####################  Exceptions
class OEBaseException(Exception):
    def __init__(self, *args, **kwargs):
        lkw = ["%s: %s" % (str(k), str(v)) for k, v in kwargs]
        Exception.__init__(self, *(args + tuple(lkw)))


class BlockChainError(OEBaseException):
    pass


####################  Blockchain building blocks
class SITransaction(object):
    """
    only record the first input of all input addresses
    """

    def __init__(self, input_address, outputs, hash):
        """
        :type input_address: str
        :type outputs: list of tuple
        :param outputs: list of (n, address, amount)
        :type hash: str
        """
        self.input_address = input_address
        self.outputs = outputs
        self.hash = hash

    def __str__(self):
        return 'input_address: %s, outputs: %s, hash: %s' % (self.input_address, str(self.outputs), self.hash)


class Block(object):
    def __init__(self, height, hash, previous_hash, transactions, timestamp):
        """
        :type height: int
        :type hash: str
        :type previous_hash: str
        :type transactions: list of SITransaction
        :type timestamp: Datetime
        """
        self.height = height
        self.hash = hash
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp

    def __str__(self):
        return 'height: %d, hash: %s, previous_hash: %s, timestamp: %s, transactions: %s' % (
            self.height, self.hash, self.previous_hash, str(self.timestamp), str(self.transactions))


class Request(object):  # base class for all requests
    STATE_NOT_PROCESSED = 0
    STATE_OK = 1
    STATE_FATAL = 2
    STATE_IGNORED_SINCE_EXCHANGE_PAUSED = 3
    STATE_IGNORED_SINCE_ASSET_PAUSED = 4
    STATE_NOT_AS_EXPECTED = 5

    def __init__(self, transaction, block_timestamp):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        """
        self.transaction = transaction
        self.block_timestamp = block_timestamp

        self.state = self.__class__.STATE_NOT_PROCESSED
        self.message = None
        self.related_payments = {}

    @classmethod
    def ignored_request(cls, transaction, block_timestamp, state):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type state: int
        """
        req = cls(transaction, block_timestamp)
        req.state = state
        return req


class CreateAsset(Request):
    # message ids starts from 10000
    MSG_ASSET_ALREADY_REGISTERED = 10000
    MSG_INPUT_ADDRESS_NOT_LEGIT = 10001

    def __init__(self, transaction, block_timestamp, file_id):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type file_id: int
        """
        super(CreateAsset, self).__init__(transaction, block_timestamp)
        self.file_id = file_id


class ExchangeStateControl(Request):
    STATE_RESUME = 1
    STATE_PAUSE = 2

    # message ids starts from 10000
    MSG_STATE_NOT_SUPPORTED = 10000
    MSG_INPUT_ADDRESS_NOT_LEGIT = 10001

    def __init__(self, transaction, block_timestamp, state):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type state: int
        """
        super(ExchangeStateControl, self).__init__(transaction, block_timestamp)
        self.state = state


class TradeItem(object):
    def __init__(self, unit_price, amount, timestamp, trade_type):
        """
        :type unit_price: int
        :type amount: int
        :type timestamp: datetime
        """
        self.unit_price = unit_price
        self.amount = amount
        self.timestamp = timestamp
        self.trade_type = trade_type


class CanceledTrade(TradeItem):  # the trade is canceled
    def __init__(self, timestamp):
        TradeItem.__init__(self, None, None, timestamp, None)


class BuyLimitOrder(Request):

    # message ids starts from 10000
    MSG_ZERO_VOLUME = 10000
    MSG_UNIT_PRICE_ILLEGIT = 10001

    def __init__(self, transaction, block_timestamp, user_address, order_index, volume, unit_price):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type user_address: str
        :param order_index: every order of a user has a unique index
        :type order_index: int or None
        :type volume: int
        :type unit_price: int or None
        """
        super(BuyLimitOrder, self).__init__(transaction, block_timestamp)

        self.user_address = user_address
        self.order_index = order_index
        self.volume_requested = volume
        self.volume_unfulfilled = volume
        self.unit_price = unit_price

        self.trade_history = []
        """:type: list of TradeItem"""


class SellLimitOrder(Request):

    # message ids starts from 10000
    MSG_ZERO_VOLUME = 10000
    MSG_UNIT_PRICE_ILLEGIT = 10001
    MSG_USER_DOES_NOT_EXISTS = 1002
    MSG_NOT_ENOUGH_ASSET = 1003

    def __init__(self, transaction, block_timestamp, user_address, order_index, volume, unit_price):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type user_address: str
        :param order_index: every order of a user has a unique index
        :type order_index: int or None
        :type volume: int
        :type unit_price: int or None
        """
        super(SellLimitOrder, self).__init__(transaction, block_timestamp)

        self.user_address = user_address
        self.order_index = order_index
        self.volume_requested = volume
        self.volume_unfulfilled = volume
        self.unit_price = unit_price

        self.trade_history = []
        """:type: list of TradeItem"""


class BuyMarketOrder(Request):

    # message ids starts from 10000
    MSG_ZERO_TOTAL_PRICE = 10000

    def __init__(self, transaction, block_timestamp, user_address, total_price):
        """
        buy market order won't have order index since it will be executed immediately, not possible to cancel
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type user_address: str
        :param total_price: total money for buying at market, will try to spend them all.(amount is always integer)
        :type total_price: int
        """
        super(BuyMarketOrder, self).__init__(transaction, block_timestamp)

        self.user_address = user_address
        self.total_price_requested = total_price

        self.total_price_unfulfilled = total_price
        self.volume_fulfilled = 0

        self.trade_history = []
        """:type: list of TradeItem"""


class SellMarketOrder(Request):

    # message ids starts from 10000
    MSG_ZERO_TOTAL_VOLUME = 10000
    MSG_USER_DOES_NOT_EXISTS = 10001
    MSG_AVAILABLE_ASSET_NOT_ENOUGH = 10002

    def __init__(self, transaction, block_timestamp, user_address, volume):
        """
        sell market order won't have order index since it will be executed immediately, not possible to cancel
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type user_address: str
        :type volume: int
        """
        super(SellMarketOrder, self).__init__(transaction, block_timestamp)
        self.user_address = user_address
        self.volume_requested = volume

        self.volume_unfulfilled = volume
        self.price_total_sold = 0  # money total sold, not volume

        self.trade_history = []
        """:type: list of TradeItem"""


class ClearOrder(Request):

    # message ids starts from 10000
    MSG_USER_DOES_NOT_EXISTS = 10000
    MSG_INDEX_IS_ZERO = 10001
    MSG_ORDER_DOES_NOT_EXIST = 10002

    def __init__(self, transaction, block_timestamp, user_address, index):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type user_address: str
        :type index: int
        """
        super(ClearOrder, self).__init__(transaction, block_timestamp)
        self.user_address = user_address
        self.index = index


class Transfer(Request):

    # message ids starts from 10000
    MSG_USER_DOES_NOT_EXISTS = 10000
    MSG_NO_VALID_TARGET = 10001
    MSG_NOT_ENOUGH_ASSET = 10002

    def __init__(self, transaction, block_timestamp, transfer_targets):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type transfer_targets: dict from str to int
        """
        super(Transfer, self).__init__(transaction, block_timestamp)
        self.transfer_targets = transfer_targets


class CreateVote(Request):

    # message ids starts from 10000
    MSG_SENDER_IS_NOT_ISSUER = 10000
    MSG_LAST_ZERO_DAYS = 10001
    MSG_NOT_ENOUGH_ASSET = 10002

    def __init__(self, transaction, block_timestamp, expire_time, index):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type expire_time: datetime
        :type index: int
        """
        super(CreateVote, self).__init__(transaction, block_timestamp)

        self.expire_time = expire_time
        self.index = index


class VoteRequest(Request):
    """
    the name VoteRequest is to distinguish with the Vote class in Asset
    """

    # message ids starts from 10000
    MSG_SENDER_IS_NOT_LEGIT = 10000
    MSG_VOTE_CLOSED = 10001
    MSG_ALREADY_VOTED = 10002
    MSG_VOTE_DOES_NOT_EXIST = 10003

    def __init__(self, transaction, block_timestamp, index, option):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type index: int
        :type option: int
        """
        super(VoteRequest, self).__init__(transaction, block_timestamp)

        self.index = index
        self.option = option


class Pay(Request):
    def __init__(self, transaction, block_timestamp, payer, pay_amount, DPS, change):
        """
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type payer: str
        :type pay_amount: int
        :type DPS: int
        :param DPS: dividend per share
        """
        super(Pay, self).__init__(transaction, block_timestamp)

        self.payer = payer
        self.pay_amount = pay_amount
        self.DPS = DPS
        self.change = change


class AssetStateControl(Request):
    STATE_RESUME = 1
    STATE_PAUSE = 2

    # message ids starts from 10000
    MSG_STATE_NOT_SUPPORTED = 10000
    MSG_INPUT_ADDRESS_NOT_LEGIT = 10001
    MSG_CAN_NOT_REINIT_WHEN_RUNNING = 10002

    def __init__(self, transaction, block_timestamp, state):
        """
        since the state could be changed in the later, now we only record the whole state
        detailed analysis could be extend easily by users of this library
        :type transaction: SITransaction
        :type block_timestamp: datetime
        :type state: int
        """
        super(AssetStateControl, self).__init__(transaction, block_timestamp)
        self.state = state


class User(object):
    """
    user of a specific asset
    in the Exchange, all assets are in a dict from AssetName -> Asset
    in an Asset, all users are organized by a dict from address -> User
    no history management
    """
    def __init__(self):
        self.available = 0
        self.total = 0
        self.vote = {}  # vote index -> vote_value
        self.order_counter = 0
        self.active_orders = {}  # order_id -> order


class Vote(object):
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


class Asset(object):
    STATE_RUNNING = 1
    STATE_PAUSED = 2

    def __init__(self, total_shares,
                 limit_buy_address, limit_sell_address, market_buy_address, market_sell_address, clear_order_address,
                 transfer_address, pay_address, create_vote_address, vote_address, state_control_address,
                 issuer_address):
        """
        :param meta_data: any extra data that should bind to this Asset.
        :type meta_data: dict
        :return:
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

        self.sell_order_book = []  # only store ask limit orders, market order won't stay after execution
        """:type: list of SellLimitOrder"""
        self.buy_order_book = []  # only store bid limit orders, market order won't stay after execution
        """:type: list of BuyLimitOrder"""

        self.state = self.__class__.STATE_PAUSED

        self.users = {}
        """:type dict from str to User:"""
        self.votes = {}  # from vote_id to Vote
        """:type dict from int to Vote:"""


class Exchange(object):
    STATE_RUNNING = 0
    STATE_PAUSED = 1

    def __init__(self):
        import settings

        self.processed_block_height = settings.EXCHANGE_INIT_BLOCK_HEIGHT
        self.processed_block_hash = settings.EXCHANGE_INIT_BLOCK_HASH

        self.state_control_address = settings.EXCHANGE_STATE_CONTROL_ADDRESS
        self.create_asset_address = settings.EXCHANGE_CREATE_ASSET_ADDRESS
        self.open_exchange_address = settings.EXCHANGE_OPEN_EXCHANGE_ADDRESS
        self.payment_log_address = settings.EXCHANGE_PAYMENT_LOG_ADDRESS

        self.assets = {}  # dict from str to Asset
        self.state = self.__class__.STATE_PAUSED
