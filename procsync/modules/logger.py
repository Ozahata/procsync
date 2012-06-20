import logging
from logging.handlers import RotatingFileHandler, SysLogHandler
from procsync.modules import settings
from os.path import join
from sys import stderr, exc_info
from tempfile import gettempdir
from traceback import print_exception

__all__ = [ "debug", "info", "warning", "error", "critical", "exception", ]

def create_instance():
    """
    Load from django settings the necessary information to start the log.
    """
    logger = logging.getLogger(settings.INSTANCE_NAME)
    logger.setLevel(logging._levelNames[settings.LOG_LEVEL])
    if len(logger.handlers) == 0:
        type_log_handler = settings.APP_CONFIG.get_config_value("logger", "log_handler", default_value="syslog")
        if type_log_handler == "syslog":
            log_address = settings.APP_CONFIG.get_config_value("logger", "address", default_value="/dev/log")
            log_facility = settings.APP_CONFIG.get_config_value("logger", "facility", default_value="local0")
            handler = SysLogHandler(address=log_address, facility=log_facility)
            __instance_type = type_log_handler
        else:
            filename = settings.APP_CONFIG.get_config_value("logger", "filename", default_value=join(gettempdir(), settings.INSTANCE_NAME + ".log"))
            mode = settings.APP_CONFIG.get_config_value("logger", "mode", default_value="a")
            maxBytes = settings.APP_CONFIG.get_config_value("logger", "maxBytes", default_value=10485760)
            backupCount = settings.APP_CONFIG.get_config_value("logger", "backupCount", default_value=100)
            log_encoding = settings.APP_CONFIG.get_config_value("logger", "encoding", default_value=None)
            delay = settings.APP_CONFIG.get_config_value("logger", "delay", default_value=0)
            handler = RotatingFileHandler(filename, mode, maxBytes, backupCount, log_encoding, delay)
            handler_file.append(handler.stream.fileno())
        formatter = logging.Formatter(settings.LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def split_len(value, length):
    """
    Split a string in n parts with length defined.
    """
    return [value[pos:pos + length] for pos in range(0, len(value), length)]

def report(log_methods, message, is_exception=False, is_info=True, *args, **kwargs):
    """
    Print in the stderr in case the user not using fork
    """
    if message is not None:
        message_list = []
        # Check if will write or not the information
        verbose = kwargs["verbose"] if "verbose" in kwargs and isinstance(kwargs["verbose"], int) else 0
        # Because the syslog have a limit, we will split in 1024 characters
        if __instance_type is None:
            message_list.append(message)
        else:
            message_list.extend(split_len(message, 1024))
        for item in message_list:
            if verbose <= __instance_verbose:
                if is_exception:
                    __instance.exception(item, *args)
                else:
                    log_methods(item, *args)
            if not is_info:
                print >> stderr, item
                exc_type, exc_value, exc_traceback = exc_info()
                if exc_type is not None and  exc_value is not None and exc_traceback is not None and is_exception:
                    print_exception(exc_type, exc_value, exc_traceback)


handler_file = []
__instance = create_instance()
__instance_type = None
__instance_verbose = settings.APP_CONFIG.get_config_value("logger", "verbose", default_value=0)

def debug(message, *args, **kwargs):
    report(__instance.debug, message, *args, **kwargs)

def info(message, *args, **kwargs):
    report(__instance.info, message, *args, **kwargs)

def warning(message, *args, **kwargs):
    report(__instance.warning, message, is_info=False, *args, **kwargs)

def error(message, *args, **kwargs):
    report(__instance.error, message, is_info=False, *args, **kwargs)

def critical(message, *args, **kwargs):
    report(__instance.critical, message, is_info=False, is_exception=__instance_verbose > 1, *args, **kwargs)

def exception(message, *args, **kwargs):
    report(__instance.exception, message, is_info=False, is_exception=True, *args, **kwargs)
