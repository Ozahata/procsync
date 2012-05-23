Process Synchronizer
====================

*A process synchronizer that, when receive a request, willcheck if have a origin of the data and distributes for N destinations.*

Introduction
------------

The motivation behind this project was the necessity of synchronize between two
MySQL databases.
 when pass the information to the other was necessary made
some changes in the value before add in the destination.

Of course, if the synchronization was limited only to sync the fields we can 
use the replication, but in the case was: When request the information to be
synchronize, we need get some fields and make some changes in the value before 
add in the destination.
 
Idea
----

Having one unique value that identify the object, will send to a queue that the
application is looking searching for a row to process.

When this row is inserted, the thread will check if have a origin that will
contain more specific information and send this informations for N destinations
registered.

This step that was describe correspond a action to be execute that inside will
contain one origin to N destination.

Available now
-------------

### Thread (Used to monitoring a request to be process)

- MySQL (Search in a table if have some row inserted)

### Connections (Used to send the command used in the origin/destination)

- MySQL (Execute query or stored procedure)
- Python script (Call a method or a class that have a method to call)

**Note:** In the future, when have some demand for new types of threads or
connection, will be implemented and add here.

How can I get more information?
-------------------------------

Please take a look in the source that will have a directory call docs and inside
have html files (start with README-FIRST.html) that will contain the explanation
necessary, if don't please feel free to send the question that I be happy to 
answer.

Requirements
------------

- Linux
- Python 2.6+
    - python-daemon 1.5.5+
    - mysql-python 1.2.2+
    - lockfile 0.9.1+
- MySQL    
    
Instalation
-----------

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