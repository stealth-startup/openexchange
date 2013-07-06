################  logging
def get_logger(name='OEDefault', file_name=None):
    import os
    import logging
    from logging.handlers import RotatingFileHandler

    logging.root.level = logging.DEBUG
    logger = logging.getLogger(name)

    if len(logger.handlers) == 0:
        fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
        formatter = logging.Formatter(fmt)

        console_handler = logging.StreamHandler()
        if file_name is None:
            file_name = os.path.join(os.getcwd() + 'OpenExchange.log')
        file_handler = RotatingFileHandler(file_name, maxBytes=1024 * 1024 * 10, backupCount=10)

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


def write_log(logger, *args, **kwargs):
    """
    :param args:
    :param kwargs: can have a level key can be specified to indicate which logger level should be used. debug is the default level
    :return:
    """
    if 'level' in kwargs:
        log_func = getattr(logger, kwargs['level'])
        del kwargs['level']
    else:
        log_func = getattr(logger, 'debug')

    msg_list = [str(arg) for arg in args] + ["%s: %s" % (str(k), str(v)) for k, v in kwargs.iteritems()]
    message = ", ".join(msg_list)

    log_func(message)


#####################  serialization and deserialization
def save_obj(obj, file_full_name):
    import cPickle

    with open(file_full_name, 'wb') as f:
        cPickle.dump(obj, f, -1)


def load_obj(file_full_name):
    import cPickle

    with open(file_full_name, 'rb') as f:
        obj = cPickle.load(f)
    return obj


####################  timestamp and datetime transformation
from datetime import datetime

UNIX_EPOCH = datetime(1970, 1, 1, 0, 0)


def datetime_to_timestamp(utc_datetime):
    """
    our timestamp is 1000 times smaller than standard
    :type utc_datetime: datetime
    :rtype : int
    """
    delta = utc_datetime - UNIX_EPOCH
    return int(delta.total_seconds())


def timestamp_to_datetime(timestamp):
    """
    our timestamp is 1000 times smaller than standard
    :type timestamp: int
    :rtype : datetime
    """
    return datetime.utcfromtimestamp(timestamp)


####################  retrieving block from blockchain.info
def fetch_json_data(url):
    """
    read json data from url, exceptions will be raised if anywhere goes wrong
    :type url: str
    :rtype : dict or list
    """
    import json
    import urllib2

    return json.load(urllib2.urlopen(url))


def fetch_latest_block_height(url="http://blockchain.info/latestblock"):
    """
    this function returns the index of the latest generated block
    may raise exceptions
    :type url: str
    :rtype : int
    """
    return fetch_json_data(url)['height']



def fetch_latest_block_height_blockexploer():
    """
    this function returns the index of the latest generated block
    may raise exceptions
    :rtype : int
    """
    url='http://blockexplorer.com/q/testnet/getblockcount'
    return fetch_json_data(url)



def fetch_block(height):
    """
    :type height: int
    :rtype : Block
    """
    from types import Block, BlockChainError, SITransaction

    def populate(json_block):
        """
        :rtype : Block
        """
        assert json_block['height'] == height
        return Block(
            height=height,
            hash=json_block['hash'],
            previous_hash=json_block['prev_block'],
            timestamp=timestamp_to_datetime(json_block['time']),
            transactions=[
                SITransaction(
                    input_address=[input['prev_out']['addr']
                                   for input in tx['inputs'] if 'prev_out' in input and 'addr' in input['prev_out']
                    ][0],
                    outputs=sorted([ (output['n'], output['addr'], output['value'])
                             for output in tx['out'] if 'addr' in output and 'value' in output
                    ], key=lambda t: t[0]),
                    hash=tx['hash'] if 'hash' in tx else None,
                ) for tx in json_block['tx'][1:]
            ]
        )

    data = fetch_json_data("http://blockchain.info/block-height/%d?format=json" % height)

    for json_block in data['blocks']:
        if 'main_chain' in json_block and json_block['main_chain'] is True:
            return populate(json_block)
    raise BlockChainError('main chain not found')


def fetch_block_blockexplorer(height):
    """
    :type height: int
    :rtype : Block
    """
    from types import Block, BlockChainError, SITransaction

    def populate(json_block):
        """
        :rtype : Block
        """
        return Block(
            height=height,
            hash=json_block['hash'],
            previous_hash=json_block['prev_block'],
            timestamp=timestamp_to_datetime(json_block['time']),
            transactions=[
                SITransaction(
                    input_address=[input['prev_out']['addr']
                                   for input in tx['inputs'] if 'prev_out' in input and 'addr' in input['prev_out']
                    ][0],
                    outputs=sorted([ (output['n'], output['addr'], output['value'])
                             for output in tx['out'] if 'addr' in output and 'value' in output
                    ], key=lambda t: t[0]),
                    hash=tx['hash'] if 'hash' in tx else None,
                ) for tx in json_block['tx'][1:]
            ]
        )

    import re
    import urllib2

    blockhash = re.search('00000000[0-9a-fA-F]+',urllib2.urlopen('http://blockexplorer.com/testnet/b/%d' % height).read()).group()
    data = fetch_json_data("http://blockexplorer.com/testnet/rawblock/%s" % blockhash)

    return populate(data)