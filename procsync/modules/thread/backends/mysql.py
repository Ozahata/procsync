from threading import Thread, Event
from procsync.modules import settings, logger as log
from _mysql_exceptions import OperationalError
from procsync.modules.tools import format_value
from procsync.modules.process import ProcessManager
from time import sleep

def check_arguments(file_config, thread_key):
    """
    Used in the modules.configuration.ThreadConfig to identify how attributes will be necessary for this module
    """
    connection_name = file_config.get_config_value(thread_key, "connection_name", default_value=None)

    # Validating
    if connection_name is None: raise AttributeError("connection_name was not declared in [%s]" % thread_key)
    # Set and return
    return {
            "connection_name" : connection_name,
            "sp_search_row" : file_config.get_config_value(thread_key, "sp_search_row", default_value="ps_search_request"),
            "sp_update_row" : file_config.get_config_value(thread_key, "sp_update_row", default_value="ps_update_request"),
            "sp_redirect_row" : file_config.get_config_value(thread_key, "sp_redirect_row", default_value="ps_redirect_request"),
            "db_name" : file_config.get_config_value(thread_key, "db_name", default_value=None)
            }


class Manager(Thread):
    """
    Default class instantiated in the modules.thread.manager that need use the basic settings.
    """
    # List of error that considerate a system error
    # http://dev.mysql.com/doc/refman/5.5/en/error-messages-server.html
    CONFIG_MYSQL_ERROR = [1046, 1051, 1318]

    def __init__(self, attrib, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs, verbose=verbose)
        # Allow abort the thread by the manager
        self.__stop_event = Event()
        self.attrib = attrib
        self.connection_name = attrib["connection_name"]
        self.connection = settings.CONNECTION_CONFIG.get_connection_config(self.connection_name)
        if self.connection is None:
            raise ReferenceError("The connection name [%s] not exist in the list of connections." % self.connection_name)
        manager_attrib = self.connection["attrib"].copy()
        # Before pass the attributes, we need certificate the manager will have a persistent connection
        manager_attrib["persistent"] = True
        # Replace the database in case the user set to find the sp in other local
        if attrib["db_name"] is not None: manager_attrib["db"] = attrib["db_name"]
        try:
            self.manager = self.connection["backend"].Manager(**manager_attrib)
        except Exception, e:
            raise EnvironmentError("Is not possible to create the connection [%s] due [%s]" % (self.connection_name, e))

    def run(self):
        """
        Run the process and wait when don't have any
        """
        PROCESS_ID, ACTION_NAME = range(2)
        try:
            sleep_time = 0
            process = ProcessManager()
            # Execute while don't have a action to close this thread (join method)
            while not self.__stop_event.isSet():
                try:
                    have_process = self.have_request()
                    if have_process is None:
                        sleep_time = sleep_time + self.attrib["sleep_sum"] if self.attrib["sleep_limit"] > sleep_time else sleep_time
                        self.__stop_event.wait(sleep_time)
                        continue
                    else:
                        sleep_time = 0
                    for row in have_process:
                        action_name = row[ACTION_NAME]
                        action = format_value(settings.ACTION_DICT, action_name, default_value=None)
                        if action is None:
                            # Get the first column in the first row that need be the queue identify
                            self.update_request(action_name, row[PROCESS_ID], settings.CONFIG_ERROR, "Action [%s] not exist!" % action_name, 0, 180)
                            continue
                        # Check the function call
                        if action["tag"] == 'redirect':
                            # For this event we need a transaction to guarantee the replication will make for all
                            self.manager.connection.autocommit(False)
                            # update_param will call the update_request and send in case have a error
                            update_param = None
                            try:
                                for item in action["redirect_to"]:
                                    result = self.redirect_request(item, *have_process)
                                    if result != 1:
                                        raise ValueError("The replication expect that was one row affected, returned [%s]" % result)
                                # If don' had a problem, so finish the request
                                self.update_request(action_name, row[PROCESS_ID], settings.PROCESS_SUCCESS, "Success!", action["retry"], action["reprocess_time"])
                                self.manager.connection.commit()
                            except OperationalError, oe:
                                update_param = (action_name, row[PROCESS_ID], settings.ACTION_ERROR, "Action Error [%s]!" % oe, action["retry"], action["reprocess_time"])
                                self.manager.connection.rollback()
                            except Exception, e:
                                update_param = (action_name, row[PROCESS_ID], settings.SYSTEM_ERROR, "System Error [%s]!" % e, action["retry"], action["reprocess_time"])
                                self.manager.connection.rollback()
                            finally:
                                self.manager.connection.autocommit(True)
                            if update_param is not None:
                                self.update_request(*update_param)
                        elif action["tag"] == 'action':
                            main_message = "[%s/%s] - " % (self.name, action_name)
                            log.info("%s Processing: %s" % (main_message, str(row)), verbose=1)
                            # Check if have origin exist other else use the same information of have_request
                            origin = format_value(action, "origin", default_value=None)
                            if origin is None:
                                # Return to a row because we threat like a result of query
                                origin = (row,)
                            else:
                                origin, result_code, error_message = process.execute(origin, row)
                                if result_code != 0:
                                    self.update_request(action_name, row[PROCESS_ID], result_code, "Origin - %s" % (error_message,), action["retry"], action["reprocess_time"])
                                    continue
                                log.info("%s Retrieve origin: %s" % (main_message, str(origin)), verbose=1)
                            have_error = False
                            # each row that return need run in destination
                            for origin_row in origin:
                                # In case a list of error, will store the error in case of the stop_on_error = False
                                error_result = None
                                for pos, destination_item in enumerate(format_value(action, "destination_list", default_value=[])):
                                    log.info("%s Process destination: %s" % (main_message, str(pos + 1)), verbose=2)
                                    _, result_code, error_message = process.execute(destination_item, origin_row)
                                    if result_code != 0:
                                        return_error_message = "%s Process destination: %s - %s" % (main_message, str(pos + 1), error_message)
                                        have_error = True
                                        if destination_item["stop_on_error"]:
                                            self.update_request(action_name, row[PROCESS_ID], result_code, return_error_message, action["retry"], action["reprocess_time"])
                                            break
                                        else:
                                            error_result = [ result_code, return_error_message ]
                                if error_result:
                                    have_error = True
                                    self.update_request(action_name, row[PROCESS_ID], error_result[0], error_result[1], action["retry"], action["reprocess_time"])
                            if not have_error:
                                self.update_request(action_name, row[PROCESS_ID], settings.PROCESS_SUCCESS, "", action["retry"], action["reprocess_time"])
                            log.info("%s Finished%s!" % (main_message, " with error" if have_error else ""), verbose=1)
                        else:
                            self.update_request(action_name, row[PROCESS_ID], settings.CONFIG_ERROR, "Tag [%s] of [%s] not exist!" % (action["tag"], action_name), action["retry"], action["reprocess_time"])
                except OperationalError, oe:
                    if oe[0] in self.CONFIG_MYSQL_ERROR: raise oe
                    log.warning("[%s/%s] - [%s], try reconnect." % (self.name, self.connection_name, oe))
                    while not self.__stop_event.isSet():
                        try:
                            self.__stop_event.wait(settings.RETRY_SLEEP)
                            self.manager.reconnect()
                            # if don't have error, will be able to back to the process
                            log.warning("[%s/%s] reestablished" % (self.name, self.connection_name))
                            break
                        except Exception:
                            log.warning("Still have a error in [%s/%s] - Retry after %s seconds" % (self.name, self.connection_name, settings.RETRY_SLEEP))
        except:
            log.critical("Problem while ran the instance thread [%s]." % self.name)

    def join(self, timeout=None):
        """
        Executed when have a request to exit
        """
        self.__stop_event.set()
        Thread.join(self, timeout=timeout)

    def have_request(self):
        """
        Check if have some request in the queue
        """
        args = [ self.name, ]
        if self.attrib["complement"] is not None: args.extend(self.attrib["complement"])
        result = self.manager.execute_sp(self.attrib["sp_search_row"], *args)
        return None if len(result) == 0 else result

    def update_request(self, action_name, queue_id, status, message, retry, reprocess_time, retry_update=0):
        """
        Check if have some request in the queue
        retry_update is internal use.
        """
        args = [ queue_id, status, message, retry, reprocess_time ]
        result = None
        try:
            if status != 0:
                log.warning("[%s/%s] - ID: [%s] - Status [%s] - Message [%s]" % (self.name, action_name, queue_id, status, message), verbose=1)
            result = self.manager.execute_sp(self.attrib["sp_update_row"], details=True, *args)
        except OperationalError, oe:
            # Deadlock found when trying to get lock; try restarting transaction
            if oe[0] == 1213:
                if retry_update < 5:
                    # Sleep to give the time to unlock
                    sleep(0.5)
                    retry_update += 1
                    log.warning("Deadlock found, retrying [%s/5]" % retry_update)
                    return self.update_request(action_name, queue_id, status, message, retry, reprocess_time, retry_update)
                else:
                    log.critical("Was not possible to update the information, please check the process.")
            else:
                log.critical("An operation error occurred: %s" % str(oe))
        except:
            log.critical("Was not possible to record the status [%s] - [%s] in the row [%s]." % (status, message, queue_id))
        return None if result is None or len(result) == 0 else result

    def redirect_request(self, action, *args):
        """
        Redirect a action in the sync to others actions
        """
        request = [ action, ]
        request.extend(args)
        result = self.manager.execute_sp(self.attrib["sp_redirect_row"], details=True, *request)
        return result["affected_rows"]
