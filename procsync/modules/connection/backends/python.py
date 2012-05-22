from procsync.modules import settings
from procsync.modules.tools import format_value
from os.path import exists, join
from sys import path

def check_arguments(file_config, connection_key):
    """
    Used in the modules.configuration.ConnectionConfig to identify how attributes will be necessary for this module
    """
    # Set and return
    return {
            "path": file_config.get_config_value(connection_key, "path", default_value=settings.PYTHON_PATH),
            }

class Manager():

    def __init__(self, *args, **kwargs):
        self.python_path = kwargs["path"]
        if not exists(self.python_path):
            raise ValueError("The directory [%s] not exist." % self.python_path)
        self.is_necessary_reprocess = False

    def reconnect(self, *args, **kwargs):
        """
        Try make the reconnect operation before try execute the run again.
        Return True if success.
        """
        try:
            return True
        except:
            return False

    def run(self, process, action_value, *args, **kwargs):
        """
        Will process the information passed in action_value.
        """
        python_path = format_value(process, "path", default_value=self.python_path)
        if not exists(python_path):
            raise ValueError("The directory [%s] not exist." % self.python_path)
        path_exist = python_path in path
        try:
            if not path_exist: path.append(python_path)

            # Check the module
            module = format_value(process, "module", default_value=None)
            if module is None: raise ValueError("The module was not set in %s that use the connection [%s]" % (process["tag"], process["connection_name"]))
            if not (exists(join(python_path, module + ".py")) or exists(join(python_path, module + ".pyc"))):
                raise ValueError("The module [%s] not exist in the path [%s]" % (module, python_path))
            class_name = format_value(process, "class", default_value=None)
            method = format_value(process, "method", default_value="run")
            module_ref = __import__(module, fromlist=None if class_name is None else [class_name, ])
            instance = (None, 1, "Was not implemented yet!")
            if class_name:
                class_ref = getattr(module_ref, class_name)()
                instance = getattr(class_ref, method)(process, action_value, *args, **kwargs)
            else:
                instance = getattr(module_ref, method)(process, action_value, *args, **kwargs)
            return instance
        except Exception, e:
            return (None, settings.SYSTEM_ERROR, e)
        finally:
            if not path_exist: path.remove(python_path)
