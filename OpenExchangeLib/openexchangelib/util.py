################  logging
def get_logger(name='OEDefault', **kwargs):
    import os
    import logging
    from logging.handlers import RotatingFileHandler

    logging.root.level = logging.DEBUG
    logger = logging.getLogger(name)

    if len(logger.handlers) == 0:
        fmt = '%(asctime)s - %(message)s'
        formatter = logging.Formatter(fmt)

        console_handler = logging.StreamHandler()
        file_name = kwargs.get('file_name')
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
    can specify log level and blank_lines in kwargs
    """
    import inspect

    caller_info = inspect.getframeinfo(inspect.stack()[1][0])
    caller_file_name = caller_info.filename.split('/')[-1]
    caller_function_name = caller_info.function
    caller_line_no = caller_info.lineno

    log_func = getattr(logger, kwargs.get('level', 'debug'))
    blank_lines = '\n' * kwargs.get('blank_lines', 0)

    if 'blank_lines' in kwargs:
        del kwargs['blank_lines']
    msg_prefix = "%s:%d - %s\n" % (caller_file_name, caller_line_no, caller_function_name)
    message = ", ".join([str(arg) for arg in args] + ["%s: %s" % (str(k), str(v)) for k, v in kwargs.iteritems()])
    log_func(msg_prefix + message + blank_lines)


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