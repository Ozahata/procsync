Process Synchronizer
====================

*Synchronizes operations between two ends, or from an origin to N destinations.*

This is particularly useful for operations, such as:

* complex database replication processes (eg. replication must be done with 
re-mapping or re-formatting of data)
* external triggers for queue-based processing (eg. an addition of a record 
on a database table must then execute another sequence of commands, not 
necessarily database related)
* and if you dare, simple database replication


Introduction
------------

The motivation behind this project started out from the necessity for 
synchronization between two MySQL databases, in which the information
being replicated needed to be properly re-shaped to adapt to the replicated
destination.

In deed, if there is no need for such complex replication methods, a simple
MySQL replication feature should do just fine. Nevertheless, this can also be
used to monitor or adjust to a row/column level on what is supposed to be 
synchronized or replicated to a destination (or multiple destinations). 

 
Idea
----

The process basically depends on queuing a particular unique object (if 
database table, should be the PK), to be processed, i.e., synchronized to
a particular destination. Once queued, the threaded worker process will 
obtain the complete dataset of information (customizable in configuration
level), manipulate it and store it in the destination (if a database), or
multiple destinations.

Instead of database objects, this also support scripts, which can be triggered
by a simple queued item or a scheduled (cronjob alike continuous processing). 


What is available now?
----------------------

### Threading (used to monitor requests to be processed)

* depends on MySQL (queries a table for unprocessed rows)

### Connections (used to send the command used in the origin/destination)

  * can be:
    * MySQL (executes a query or stored procedure)
    * Python script (aall a method or a class using specified access interface)

**Note**: There are infinite ways to improve this part, which will be done as 
demand suggests or requests for it.


How can I get more information?
-------------------------------

Please take a look in the source directory **docs/** for a more comphrehensive 
documentation (start with README-FIRST.html). But if you feel it is not enough,
feel free to drop me a line at anytime.


Requirements
------------

* Linux
* Python 2.6+
    * python-daemon 1.5.5+
    * mysql-python 1.2.2+
    * lockfile 0.9.1+
* MySQL    
 
   
Install
-------

1. Download the Source 
[here](https://github.com/Ozahata/procsync/zipball/master)
2. Unpack it
     
        unzip Ozahata-procsync-{identify}.zip

3. Install it

        sudo python setup.py install 
        
3. Configure

        Please check the documentation for more details.
        
Uninstall
---------

Just remove manually the following files:

        rm -rvf /usr/local/bin/run_sync.py 
        rm -rvf /usr/local/lib/python2.X/dist-packages/procsync-0.* 

**Note:** The "X" means the version of python that you use.