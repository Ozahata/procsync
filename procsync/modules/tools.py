from os.path import join, realpath, exists
from os import getcwd
from sys import stderr
from ConfigParser import RawConfigParser, NoOptionError, NoSectionError

class Config:
    """
    Provides configuration utilities for applications or scripts.

    This will use the `ConfigParser` module to read configuration information
    from a specific file (ini file), formatted under the python ini
    file standards.

    The location of the file should be:

        Your app/
            |
            |-- zzz/ (this library)
            |   |
            |   |-- util.py (this module)
            |
            |-- app.conf (the configuration file)

    * same path of this current library code (parent path of the current file)

    * configuration file name as: [app.conf].

    Usage example:

        cfg = Config()
        value = cfg.get_config_value("section", "key")

    See construction `__init__` for more details on class instantiation
    and variations.

    """

    def __init__(self, path=None, file_name=None):
        """
        Initialize the variable and the basic stuff

        Arguments
        ---------

            - @path::        path where the file is it.
            - @file_name::   name of file to load the config (use by default
                             the extention ".conf" in the end)
        """
        # Define the configuration file path
        self._file_name = join(realpath(getcwd()) if path is None else path, "app.conf" if file_name is None else file_name)
        if not exists(self._file_name): raise IOError("File [%s] that use to load configurations, not exist." % self._file_name)
        try:
            # Instantiate the config parser
            self._config = RawConfigParser()
            self._config.read(self._file_name)
        except:
            # terminate the program in case there are any errors here!
            raise SystemExit("Unable to properly instantiate the" \
                " configuration file. Make sure the file [%s] exists and" \
                " contains proper settings your application may need to run." \
                % self._file_name)

    def get_config_value(self, section, key, default_value=None, return_type=None, ignore_errors=True, empty_become_none=False, *args, **kw):
        """
        Gets the value of a key in the configuration file.

        Arguments
        ---------

            - @section::  The section of the file (see notes below)

            - @key:: The key that represents the value you need.
            
            - @return_type:: In case of necessity of a specific return

            - @default_value::   Return this value if the request don't have a 
                     value to return or is empty.
                     Default is empty.
        Returns
        -------

            This method returns the value object (string) retrieved from
            configuration file, and corresponding to the key as specified.
        """
        return_value = None
        try:
            return_type = (None if default_value is None else type(default_value)) if return_type is None else return_type
            return_value = convert_value(self._config.get(section, key), return_type)
            if empty_become_none and return_value is not None and return_value == "":
                return_value = None
        except (NoOptionError, NoSectionError):
            return_value = default_value
        except Exception, e:
            if ignore_errors:
                print >> stderr, 'Could not get config value for section=[%s], key=[%s]. Just ignoring. [%s]' % (section, key, e)
            else:
                raise e
        return return_value

def convert_value(value, return_type, convert_null_to_string=False):
    """
    Convert the value to the type request.
    convert_null_to_string    When the request for some reason come null, will change to empty string
    """
    if return_type == None: return_type = str
    if value is None:
        if convert_null_to_string == True:
            value = ""
        else:
            return None
    # The bool is important that come before int because (True/False) can be interpreted like int)
    if return_type == bool:
        value = value.lower() == "true" or value == "1" if isinstance(value, basestring) else value == 1
    elif return_type == int:
        # Have a case that the string can be true/false so transform to 0 or 1
        if isinstance(value, basestring) and value.lower() in ["true", "false"]:
            value = 0 if value.lower() == "false" else 1
        else:
            value = 0 if value is None or value == "" else int(value)
    elif return_type == long:
        # Have a case that the string can be true/false so transform to 0 or 1
        if isinstance(value, basestring) and value.lower() in ["true", "false"]:
            value = 0L if value.lower() == "false" else 1L
        else:
            value = 0L if value is None or value == "" else long(value)
    elif return_type == float:
        value = 0 if value is None or value == "" else float(value)
    elif return_type == unicode and not isinstance(value, unicode):
        try:
            value = unicode(value)
        except:
            # Have a possibility that the string have the kanji/etc, so need convert and after make unicode
            value = unicode(value.decode("utf-8"))
    else:
        try:
            value = str(value)
        except:
            # Have a possibility that the unicode kanji/etc, so need convert before turn string
            value = value.encode("utf-8")
    return value

def format_value(dictionary, key, default_value=None, is_include_empty=True, return_type=None, is_return_nfsw=False):
    """
    Search in the request by method submitted the key and return the value in the
       format requested.
    Parameters:
    dictionary        Dictionary that wish get some information.
                         Note: If the request is null, the value return will be null.
    key               Key that will search in the request.
                         Note: If the key is null, the value return will be null.
    default_value     In case that found the key but the value is null (or empty if is_include_empty=True)
                         will return this value instead the null (Remember the default is null).
    is_include_empty  If true will return the default_value when null or empty, in case false the
                         default_value will return only in case the value is null.
    return_type       In case that wish return the information different of string, input the type
                         you wish return.
    is_return_nfsw    Return null for string that contain None, null, undefined.   
                        
    """
    # If don't have dictionary or key don't make nothing
    if dictionary is None or key is None: return None
    return_value = dictionary[key] if key in dictionary and not (is_return_nfsw and dictionary[key].lower() in ["null", "none", "undefined"]) else None
    type_request = None
    if default_value is not None:
        if return_type is None:
            type_request = type(default_value)
        else:
            type_request = return_type if return_type else type(return_value)
    else:
        type_request = return_type if return_type else type(return_value)
    # Default validation
    if return_value is None or (is_include_empty and return_value == ""):
        return_value = default_value
    return return_value if isinstance(return_value, type_request) else convert_value(return_value, type_request)
