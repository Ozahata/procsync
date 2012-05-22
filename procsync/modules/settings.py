from procsync.modules.tools import Config
from procsync.modules.dxml import ActionDict
from procsync.modules.configuration import ThreadConfig, ConnectionConfig
from os import getcwd
from os.path import join

PROCESS_SUCCESS, CONFIG_ERROR, ACTION_ERROR, SYSTEM_ERROR = range(4)

APP_CONFIG = Config()

INSTANCE_NAME = APP_CONFIG.get_config_value("application", "name", default_value="Not defined")
MANAGER_SLEEP = APP_CONFIG.get_config_value("application", "manager_sleep", default_value=5.0)
RETRY_SLEEP = APP_CONFIG.get_config_value("application", "retry_sleep", default_value=5.0)
SCRIPT_PATH = APP_CONFIG.get_config_value("application", "script_path", default_value=join(getcwd(), "scripts"))

MYSQL_UNIX_SOCKET = APP_CONFIG.get_config_value("mysql", "unix_socket", default_value=None)

PYTHON_PATH = APP_CONFIG.get_config_value("python", "path", default_value=join(getcwd(), "scripts", "python"))

LOG_FORMAT = APP_CONFIG.get_config_value("logger", "format", default_value="[%(process)d/%(thread)d/%(name)s] %(levelname)s: %(message)s")
LOG_LEVEL = APP_CONFIG.get_config_value("logger", "log_level", default_value="ERROR").upper()

ACTION_FILE_NAME = APP_CONFIG.get_config_value("files", "actions", default_value="ActionList.xml")
ACTION_DICT = ActionDict(ACTION_FILE_NAME)

CONNECTION_FILE_NAME = APP_CONFIG.get_config_value("files", "connections", default_value="connection.conf")
CONNECTION_CONFIG = ConnectionConfig(CONNECTION_FILE_NAME)

THREAD_FILE_NAME = APP_CONFIG.get_config_value("files", "threads", default_value="thread.conf")
THREAD_CONFIG = ThreadConfig(THREAD_FILE_NAME)
