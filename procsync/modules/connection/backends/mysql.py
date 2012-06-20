from _mysql_exceptions import OperationalError
from contextlib import closing
from datetime import datetime, timedelta
from getpass import getuser
from procsync.modules import settings, logger as log
from procsync.modules.tools import format_value
from sys import exit
from warnings import filterwarnings
filterwarnings("ignore", "No data .*")
try:
    import MySQLdb
except:
    log.critical("The application need the module mysqldb to run.\nSee: http://sourceforge.net/projects/mysql-python/")
    exit(1)

def check_arguments(file_config, connection_key):
    """
    Used in the modules.configuration.ConnectionConfig to identify how attributes will be necessary for this module
    """
    # Set and return
    return {
            "host" : file_config.get_config_value(connection_key, "host", default_value=None),
            "port" : file_config.get_config_value(connection_key, "port", default_value=3306),
            "user" : file_config.get_config_value(connection_key, "user", default_value=getuser()),
            "passwd" : file_config.get_config_value(connection_key, "passwd", default_value=None),
            "db" : file_config.get_config_value(connection_key, "db", default_value=None),
            "unix_socket" : file_config.get_config_value(connection_key, "unix_socket", default_value=settings.MYSQL_UNIX_SOCKET),
            "connect_timeout" : file_config.get_config_value(connection_key, "connect_timeout", default_value=None, return_type=int),
            "persistent" : file_config.get_config_value(connection_key, "persistent", default_value=False),
            "wait_timeout" : file_config.get_config_value(connection_key, "wait_timeout", default_value=28800),
            "retry_sleep" : file_config.get_config_value(connection_key, "retry_sleep", default_value=settings.RETRY_SLEEP),
            }

class Manager():

    def __init__(self, *args, **kwargs):
        self.attrib = dict([ (key, value) for key, value in kwargs.iteritems() if value is not None and key in ["host", "port", "user", "passwd", "db", "unix_socket", "connect_timeout"] ])
        self.connection = None
        self.is_persistent = kwargs["persistent"]
        self.is_necessary_reprocess = False
        # Subtract 5 seconds to have time to ping again and avoid disconnection
        # Of course if call before the time expire. 
        self.wait_timeout = kwargs["wait_timeout"] - 5
        self.connect_time = datetime.now() + timedelta(0, self.wait_timeout)
        self.retry_sleep = kwargs["retry_sleep"]

    def connect(self, force_connect=False):
        if self.is_persistent and self.connect_time < datetime.now():
            try:
                self.connection.ping()
                # Used to wait_timeout if is_persistent
                self.connect_time = datetime.now() + timedelta(0, self.wait_timeout)
            except:
                force_connect = True
        if self.connection is None or self.connection.open == 0 or force_connect:
            self.connection = MySQLdb.connect(**self.attrib)
            # The MySQLdb set the auto commit to 0, we need change 
            self.connection.autocommit(True)
        return self.connection

    def reconnect(self, *args, **kwargs):
        """
        Try make the reconnect operation before try execute the run again.
        Return True if success.
        """
        try:
            self.connect(force_connect=True)
            self.connection.ping()
            # Used to wait_timeout if is_persistent
            self.connect_time = datetime.now() + timedelta(0, self.wait_timeout)
            self.is_necessary_reprocess = False
            return True
        except:
            return False

    def execute(self, query, *args, **kwargs):
        connection = self.connect()
        try:
            # If connection is permanent is possible that have many changes of db
            db = format_value(kwargs, "db", default_value=format_value(self.attrib, "db", default_value=""))
            connection.select_db(db)
            result = None
            with closing(connection.cursor()) as cursor:
                if format_value(kwargs, "is_sp", default_value=False):
                    cursor.callproc(query, args)
                else:
                    cursor.execute(query, args)
                if format_value(kwargs, "details", default_value=False):
                    result = {
                              "affected_rows": connection.affected_rows(),
                              "insert_id": connection.insert_id(),
                              }
                else:
                    result = cursor.fetchall()
            # Used to wait_timeout if is_persistent
            self.connect_time = datetime.now() + timedelta(0, self.wait_timeout)
            # Log the warning information
            for item in connection.show_warnings():
                # 1329L, 'No data - zero rows fetched, selected, or processed'
                if item[1] == 1329:
                    log.debug(item[2])
                else:
                    log.warning("%s - %s" % (item[1], item[2]))
            return result
        except OperationalError, oe:
            # Range >999 used to client error codes
            self.is_necessary_reprocess = oe[0] > 9999
            raise oe
        except Exception, e:
            raise e
        finally:
            self.close()

    def execute_sp(self, query, *args, **kwargs):
        return self.execute(query, *args, is_sp=True, **kwargs)

    def close(self, force_close=False):
        if not self.is_persistent or force_close: self.connection.close()

    def run(self, process, action_value, *args, **kwargs):
        """
        Will process the information passed in action_value.
        """
        field_position = format_value(process, "field_position", default_value=None)
        run_method = format_value(process, "run_method", default_value="query" if process["tag"] == "origin" else "update").lower()
        query = format_value(process, "text", default_value="")
        try:
            values = action_value if field_position is None else tuple([ action_value[item] for item in field_position ])
        except:
            # Probably the action value don't have all the items  
            return (None, 1, "Values not compatible with field_positions!")
        other_settings = {}
        db = format_value(process, "db_name", default_value=None)
        if db is not None: other_settings["db"] = db
        other_settings["details"] = run_method in [ "update", "sp_update" ]
        other_settings["run_method"] = run_method in [ "sp", "sp_update" ]
        try:
            result = self.execute(query, is_sp=run_method == "sp", *values, **other_settings)
            if run_method in [ "update", "sp_update" ]:
                result = (result["affected_rows"], result["insert_id"])
            return (result, 0, "Success!")
        except OperationalError, oe:
            # Range >999 used to client error codes
            # 1205, 1213 - lock tables (Valid only to MySQL 5.5+)
            # 2002, 2006, 2010, 2011, 2013, 2015, 2026, 2055 - Connection 
            is_connection_problem = (oe[0] in [1205, 1213, 2002, 2006, 2010, 2011, 2013, 2015, 2026, 2055])
            is_user_problem = oe[0] > 9999
            self.is_necessary_reprocess = is_user_problem or is_connection_problem
            return (None, settings.ACTION_ERROR if is_user_problem else settings.CONNECTION_ERROR if is_connection_problem else settings.SYSTEM_ERROR, "Problem when executed the row [%s]!" % oe[1])
        except Exception, e:
            return (None, settings.ACTION_ERROR, "Problem when executed the row [%s]!" % e)

