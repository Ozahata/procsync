from procsync.modules.tools import Config
from os.path import exists
from procsync.modules.dxml import ActionDict
from copy import copy

class ThreadConfig():

    def __init__(self, file_name):
        self.file_name = file_name
        if not exists(file_name):
            raise StandardError("The file that contain the action list [%s] was not created" % file_name)
        self.file_config = Config(file_name=file_name)
        # Initialize thread list (run_list)
        self.run_list = self.file_config.get_config_value("application", "run_list", default_value=None, empty_become_none=True)
        session_list = [ item for item in self.file_config._config.sections() if item != "application" ]
        if self.run_list is None:
            self.run_list = session_list
        else:
            self.run_list = [ item.strip() for item in self.run_list.split(",") if item.strip() != "" ]
            # alert for wrong thread
            for item in self.run_list:
                if item not in session_list: raise ValueError("The item in the run_list [%s] not exist in the thread file session" % item)
        # Prepare to load the thread(s)
        self.thread_list = {}

    def _load_pool(self):
        """
        Due the module.settings can't be imported (circular reference) we need call after from a method.
        """
        from procsync.modules import settings
        load_thread_list = list(self.run_list)
        for item in load_thread_list:
            # Load the backends to run the process
            backends = self.file_config.get_config_value(item, "backend", default_value="procsync.modules.thread.backends.mysql")
            try:
                # Plus one to jump the dot and get the module name
                backends = __import__(backends, fromlist=[backends[backends.rfind(".") + 1:], ])
            except Exception, e:
                raise ReferenceError("The module [%s] threw a error when tried import [%s]: [%s]" % (backends, item, e))
            # Check if all arguments necessary for the thread was declared
            attrib = backends.check_arguments(self.file_config, item)
            attrib["backend"] = backends
            # Load the basic information common for all thread backends
            complement = self.file_config.get_config_value(item, "complement", default_value=None, empty_become_none=True)
            attrib["complement"] = complement if complement is None else [ item_complement.strip() for item_complement in complement.split(",") ]
            attrib["sleep_sum"] = self.file_config.get_config_value(item, "sleep_sum", default_value=0.5)
            attrib["sleep_limit"] = self.file_config.get_config_value(item, "sleep_limit", default_value=5.0)
            action_file = self.file_config.get_config_value(item, "action_file", default_value=None, empty_become_none=True)
            attrib["action_file"] = settings.ACTION_DICT if action_file is None else ActionDict(action_file)
            self.thread_list[item] = attrib
            # Replicate if necessary
            replicate = self.file_config.get_config_value(item, "replicate", default_value=0, empty_become_none=True)
            if replicate > 0:
                for thread_item in range(replicate):
                    thread_name = item + ("_%s" % (thread_item + 1,))
                    self.thread_list[thread_name] = copy(attrib)
                    self.run_list.append(thread_name)

    def get_thread_list(self):
        return self.run_list

    def get_thread_config(self, thread_name):
        if len(self.thread_list) < len(self.run_list): self._load_pool()
        return self.thread_list[thread_name] if thread_name in self.thread_list else None

class ConnectionConfig():

    def __init__(self, file_name):
        if not exists(file_name):
            raise StandardError("The file that contain the action list [%s] was not created" % file_name)
        self.file_config = Config(file_name=file_name)
        # Prepare the connection(s)
        self.connection_list = {}
        # Inform that need call the method to load the connections
        self.connection_are_loaded = False

    def _load_connection(self):
        """
        Due the module.settings can't be imported (circular reference) we need call after from a method.
        The import is use by check_arguments.
        """
        # For each connection we will check if the configuration is ok.
        for item in self.file_config._config.sections():
            # Load the backends to run the process
            backends = self.file_config.get_config_value(item, "backend", default_value="procsync.modules.connection.backends.mysql")
            try:
                # Plus one to jump the dot and get the module name
                backends = __import__(backends, fromlist=[backends[backends.rfind(".") + 1:], ])
            except Exception, e:
                raise ReferenceError("The module [%s] threw a error when tried import [%s]: [%s]" % (backends, item, e))
            # Check if all arguments necessary for the thread was declared
            attrib = backends.check_arguments(self.file_config, item)
            self.connection_list[item] = {
                                          "backend" : backends,
                                          "attrib" : attrib
                                          }
        self.connection_are_loaded = True

    def get_connection_config(self, connection_name):
        if not self.connection_are_loaded: self._load_connection()
        return self.connection_list[connection_name] if connection_name in self.connection_list else None
