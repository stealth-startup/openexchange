from threading import Lock
from openexchangelib import types as oel_types
import os
import data_management as dm


class ChainedStateNotInitError(oel_types.OEBaseException):
    pass


class ChainedState(object):
    _lock = Lock()
    _global_instance = None
    """:type: ChainedState"""

    def __init__(self, lib_exchange, **kwargs):
        """
        :type lib_exchange: oel_types.Exchange
        """
        assert isinstance(lib_exchange, oel_types.Exchange)
        self.exchange = lib_exchange

        #user_history[asset_name][user_address] is a list
        self.user_history = kwargs.get('user_history', {})
        self.asset_history = kwargs.get('asset_history', {})
        """:type: dict from str to list"""
        self.exchange_history = kwargs.get('exchange_history', [])
        """:type: list"""
        self.failed_requests = kwargs.get('failed_requests', [])
        """:type: list"""
        self.recent_trades = kwargs.get('recent_trades', {})
        """:type: dict from str to list of TradeItem"""
        self.order_book = kwargs.get('order_book', {})
        """:type: dict"""
        self.chart_data = kwargs.get('chart_data', {})
        """:type: dict"""
        self.used_asset_init_ids = kwargs.get('used_asset_init_ids', set())
        """:type: set"""

    @classmethod
    def acquire_lock(cls):
        cls._lock.acquire()

    @classmethod
    def release_lock(cls):
        cls._lock.release()

    @classmethod
    def get_latest_state(cls):
        if cls._global_instance:
            height = cls._global_instance.exchange.processed_block_height
            if not os.path.isfile(os.path.join(dm.BLOCK_FOLDER, str(height+1))):
                return cls._global_instance

        latest_cs = dm.pop_chained_state()
        if latest_cs is None:
            raise ChainedStateNotInitError()
        else:
            cls.acquire_lock()
            cls._global_instance = latest_cs
            cls.release_lock()
        return cls._global_instance

    def __str__(self):
        return "Exchange: %s\nUser history: %s\nAsset history: %s\nExchange history: %s\nFailed requests: %s\n" \
               "Recent trades:%s\nOrder book: %s\nChart data: %s\nUsed asset init IDs: %s\n" % \
               (str(self.exchange), str(self.user_history), str(self.asset_history), str(self.exchange_history),
               str(self.failed_requests), str(self.recent_trades), str(self.order_book), str(self.chart_data),
               str(self.used_asset_init_ids))

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return str(self)


class StaticData(object):
    """
    data have nothing to do with bitcoin block chain
    """
    _lock = Lock()
    _global_instance = None
    """:type: StaticData"""

    def __init__(self, **kwargs):
        """
        :type lib_exchange: oel_types.Exchange
        """
        #add static data here
        self.asset_descriptions = kwargs.get('asset_descriptions', {})

    @classmethod
    def acquire_lock(cls):
        cls._lock.acquire()

    @classmethod
    def release_lock(cls):
        cls._lock.release()

    @classmethod
    def get_static_data(cls):
        if cls._global_instance:
            return cls._global_instance

        sd = dm.load_static_data()
        cls.acquire_lock()
        cls._global_instance = sd
        cls.release_lock()

        return cls._global_instance


class UserPayLog(object):
    def __init__(self, transaction, block_timestamp, DPS, share_N):
        """
        :type transaction: Transaction
        :type block_timestamp: datetime
        :type DPS: int
        :param DPS: dividend per share
        :type share_N: int
        :param share_N: the number of shares user holds at that time
        """
        self.transaction = transaction
        self.block_timestamp = block_timestamp
        self.DPS = DPS
        self.share_N = share_N

    def __str__(self):
        return "transaction: %s\nblock_timestamp: %s\nDPS: %s\nshare_N: %s\n" % \
               (str(self.transaction), str(self.block_timestamp), str(self.DPS), str(self.share_N))

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return str(self)