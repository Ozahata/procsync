from procsync.modules import settings
from datetime import datetime, timedelta

class ProcessManager():
    """
    The process manager have the function to execute and manager the connections.
    """

    def __init__(self):
        # Connections that use by the process
        self.connections = {}
        # Will use to store the connection_name with key and with a list that contain
        # the time to re-process and the error message.
        self.wait_reconnect = {}

    def get_connection(self, connection_name):
        if connection_name not in self.connections.keys():
            connection = settings.CONNECTION_CONFIG.get_connection_config(connection_name)
            if connection is None:
                raise ReferenceError("The connection name [%s] not exist in the list of connections." % connection_name)
            self.connections[connection_name] = connection["backend"].Manager(**connection["attrib"])
        return self.connections[connection_name]

    def execute(self, process, action_value):
        """
        Get a dictionary that have the information necessary to process the information
        """
        try:
            connection_name = process["connection_name"]
            connection = self.get_connection(connection_name)
            # Check if necessary reconnect.
            if connection_name in self.wait_reconnect.keys():
                if self.wait_reconnect[connection_name] > datetime.now():
                    if connection.reconnect():
                        del self.wait_reconnect[connection_name]
                    else:
                        self.wait_reconnect[connection_name] = datetime.now() + timedelta(0, getattr(connection, "retry_sleep", settings.RETRY_SLEEP))
                        return (None, settings.SYSTEM_ERROR, "Reconnect fail!")
            result = connection.run(process, action_value)
            # Check if need reconnect
            if connection.is_necessary_reprocess:
                self.wait_reconnect[connection_name] = datetime.now() + timedelta(0, getattr(connection, "retry_sleep", settings.RETRY_SLEEP))
            return result
        except Exception, e:
            return (None, settings.SYSTEM_ERROR, e)
