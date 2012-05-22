# dxml - Dictionary XML
from procsync.modules.tools import format_value
from os.path import exists
from xml.etree.ElementTree import ElementTree
from copy import deepcopy

class XMLParserToDict(list):
    """
    Make the first filter to get a tag and change to dictionary
    """

    def __init__(self, file_name):
        if not exists(file_name): raise IOError("The file [%s] not exist, please check before run again." % file_name)
        # Load the file
        parser = ElementTree(file=file_name)
        self.extend([self.__process(item) for item in parser.getroot() ])

    def __process(self, element):
        return {
                  "tag" : element.tag.lower(),
                  "text" : None if element.text is None else element.text.strip(),
                  "attrib" : element.attrib,
                  "list" : [self.__process(item) for item in element]
                  }

class ActionDict(dict):
    """
    Get the xml and format to the action list to be read in the process.
    """

    def __init__(self, file_name, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        if not exists(file_name):
            raise StandardError("The file that contain the action list [%s] was not created" % file_name)
        request = XMLParserToDict(file_name)
        # For the first tags
        for item in request:
            # Don't accept if don't have name of the action
            name = format_value(item["attrib"], "name", None)
            if name is None: continue
            if item["tag"] == "action":
                self._action_parse(name, item)
                # Check if have a less one destination
                if len(self[name]["destination_list"]) < 1:
                    raise StandardError("The action [%s] need have a less one destination." % name)
                # Check if request to duplicate the action
                duplicate = format_value(item["attrib"], "duplicate", "")
                if len(duplicate) > 0:
                    # Check the necessary quantity information that need be set
                    # The number 1 means the action name
                    qtd = 1 + (0 if self[name]["origin"] is None else 1)
                    dest_qtd = len(self[name]["destination_list"])
                    # First split the list of actions
                    action_list = duplicate.split(";")
                    for action in action_list:
                        if len(action) < 1: continue
                        attr = action.split(",")
                        if attr[0] == "": raise StandardError("The duplicate name in action [%s] is necessary declarate." % name)
                        if len(attr) != qtd + dest_qtd:
                            raise StandardError("The duplicate [%s] in action [%s] have incomplete information." % (attr[0], name,))
                        # Clone the dictionary
                        clone = deepcopy(self[name])
                        clone.pop("duplicate")
                        # Change the name
                        clone["name"] = attr[0]
                        if self[name]["origin"] is not None and attr[1] != "":
                            clone["origin"]["connection_name"] = attr[1]
                        for position in range(len(clone["destination_list"])):
                            if attr[qtd + position] != "":
                                clone["destination_list"][position]["connection_name"] = attr[qtd + position]
                        self[clone["name"]] = clone
                    # Remove the duplicate
                    item["attrib"].pop("duplicate")
            if item["tag"] == "replicate":
                self._replication_parse(name, item)

    def _replication_parse(self, name, element):
        attrib = element["attrib"]
        replicate_to = format_value(attrib, "to", None)
        if replicate_to is None: raise StandardError("The attribute [to] in the replicate [%s] need be declared" % name)
        replicate_to = [ item.strip() for item in replicate_to.split(",") if item.strip() != "" ]
        # Check if all the actions exist
        for action in replicate_to:
            if action not in self.keys():
                raise ValueError("The action [%s] in the replicate [%s] not exist in the action list" % (action, name))
        self[name] = {
                      "tag": element["tag"],
                      "replicate_to": replicate_to[:],
                      "reprocess_time": format_value(attrib, "reprocess_time", 180),
                      "retry": format_value(attrib, "reprocess_time", 0)
                      }

    def _action_parse(self, name, element):
        attrib = element["attrib"]
        # Validate the necessary variables
        attrib["tag"] = element["tag"]
        attrib["reprocess_time"] = format_value(attrib, "reprocess_time", 180)
        attrib["retry"] = format_value(attrib, "retry", 0)
        attrib["origin"] = None
        attrib["destination_list"] = []
        # Will be use to set a default in case have multiple destination
        attrib["stop_on_error"] = True
        self[name] = attrib
        for item in element["list"]:
            self._process_internal(name, item)
        # Each destination already have the information set, so don't need the key anymore
        self[name].pop("stop_on_error")

    def _process_internal(self, parent_name, element):
        tag = element["tag"]
        # In case of destinations just set to be a list
        if tag == "destinations":
            # In case the user set in destinations
            self[parent_name]["stop_on_error"] = format_value(element, "stop_on_error", True)
            # Call the list inside
            for item in element["list"]:
                self._process_internal(parent_name, item)
            return
        attrib = element["attrib"]
        # Adding in the attribute: tag and text to manipulate only one dictionary
        attrib["tag"] = format_value(element, "tag", None)
        attrib["text"] = format_value(element, "text", None)
        attrib["connection_name"] = format_value(attrib, "connection_name", None)
        if attrib["connection_name"] is None:
            raise ValueError("One of tag origin/destination in the action [%s] was set the run_method with query but without connection_name" % parent_name)
        # Using to origin/destination
        attrib["field_position"] = format_value(attrib, "field_position", None)
        if attrib["field_position"] is not None:
            attrib["field_position"] = [ int(item) for item in attrib["field_position"].split(",") ]
        if tag == "destination":
            attrib["stop_on_error"] = format_value(attrib, "stop_on_error", self[parent_name]["stop_on_error"])
        # Add the information in the parent_name
        if tag == "destination":
            # Check if have multiple connections
            connections = attrib["connection_name"].split(",")
            destination_list = []
            for connection in connections:
                destination = attrib.copy()
                destination["connection_name"] = connection.strip()
                destination_list.append(destination.copy())
            self[parent_name]["destination_list"].extend(destination_list)
        else:
            self[parent_name][tag] = attrib.copy()
