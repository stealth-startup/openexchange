from threading import Lock
from openexchangelib import types
import os
import data_management as dm


class ChainedStateNotInitError(types.OEBaseException):
    pass


class LPSingleton(object):  # Lockable Pickle-able Singleton
    """
    Every child of this class need to declare a class variable of Lock type named _lock, so that every child class
    has it's owe lock, and is still pickle-able (pickle doesn't watch for class variables)
    A more elegant way of implementation is to use meta-class, which I'm not familiar with yet
    """
    @classmethod
    def acquire_lock(cls):
        getattr(cls, '_lock').acquire()

    @classmethod
    def release_lock(cls):
        getattr(cls, '_lock').release()

    def __getnewargs__(self):
        """
        this method is called when doing pickle.dump. it returns a tuple indicate the args should be passed to
        __new__ when doing pickle.load
        :return:
        """
        return (True,)


class ChainedState(LPSingleton):
    """
    All data related with a block of the bitcoin block chain
    """
    _global_instance = None
    _lock = Lock()  # class variable will not be pickled, so we don't worry that a Lock is not serializable

    def __new__(cls, is_unpickling=False):
        if is_unpickling:  # return a brand new object when unpicking
            # the rest of the initialization is handled by pickle, note that the _global_instance is not set
            return super(cls, cls).__new__(cls)

        if cls._global_instance:
            height = cls._global_instance.exchange.processed_block_height
            # although there may have a short-time inconsistency when the chain rewinds, but it really doesn't matter
            if not os.path.isfile(os.path.join(dm.BLOCK_FOLDER, str(height+1))):
                return cls._global_instance

        new_cs = dm.latest_chained_state()  # TODO can be optimized by threading. using the latest data is not an necessity.
        if new_cs is None:
            raise ChainedStateNotInitError()
        else:  # a restart of the server or a new block is generated
            cls.acquire_lock()
            cls._global_instance = new_cs
            cls.release_lock()

        return cls._global_instance

    def __init__(self):  # just to add hints for the IDE's code completion
        if hasattr(self, 'exchange'):
            assert isinstance(self.exchange, types.Exchange)
        if hasattr(self, 'user_history'):  # user_history[asset_name][user_address] is a list
            assert isinstance(self.user_history, dict)
        if hasattr(self, 'asset_history'):
            asset_history = self.asset_history
            """:type: dict from str to list of Request"""
            assert isinstance(self.asset_history, dict)
        if hasattr(self, 'exchange_history'):
            exchange_history = self.exchange_history
            """:type: list of Request"""
            assert isinstance(self.exchange_history, list)
        if hasattr(self, 'failed_requests'):
            assert isinstance(self.failed_requests, list)  # list of Request
        if hasattr(self, 'recent_trades'):
            assert isinstance(self.recent_trades, dict)  # dict of list of TradeItem
        if hasattr(self, 'order_book'):
            assert isinstance(self.order_book, dict)
        if hasattr(self, 'chart_data'):
            assert isinstance(self.chart_data, dict)


class StaticData(LPSingleton):
    """
    data have nothing to do with bitcoin block chain
    """
    _global_instance = None
    _lock = Lock()

    def __new__(cls, is_unpickling=False):
        if is_unpickling:  # return a brand new object when unpicking
            # the rest of the initialization is handled by pickle, note that the _global_instance is not set
            return super(cls, cls).__new__(cls)

        if cls._global_instance:
            return cls._global_instance

        new_sd = dm.load_static_data()

        cls.acquire_lock()
        cls._global_instance = new_sd
        cls.release_lock()

        return cls._global_instance

    def __init__(self):  # just to add hints for the IDE's code completion
        if hasattr(self, 'asset_description'):
            assert isinstance(self.asset_description, dict)  # dict from str to sr


class UserPayLog(types.Request):
    def __init__(self, transaction, payer, DPS, share_N):
        """
        :type transaction: SITransaction
        :type payer: str
        :type DPS: int
        :param DPS: dividend per share
        :type share_N: int
        :param share_N: the number of shares user holds at that time
        """
        super(UserPayLog, self).__init__(transaction)
        self.payer = payer
        self.DPS = DPS
        self.share_N = share_N