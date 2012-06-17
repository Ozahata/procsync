from procsync.modules import settings, logger as log
from sys import stdout
from time import sleep
from os import getpid

class ThreadManager:

    def __init__(self):
        self.run_list = settings.THREAD_CONFIG.get_thread_list()
        self.pool = []
        self.lock = None

    def start(self):
        message = "Start the instance."
        # Use the lock to add the pid used in shell/unix service
        with open(self.lock.lock_file, "w") as lock_file:
            lock_file.write(str(getpid()))
            lock_file.flush()
        print >> stdout, message
        log.info(message)
        # Initializing the threads
        for process in self.run_list:
            # Get the thread attribute settings
            attrib = settings.THREAD_CONFIG.get_thread_config(process)
            if attrib is None: raise ReferenceError("The thread name [%s] not exist in the file [%s] or have a wrong configuration." % (process, settings.THREAD_CONFIG.file_name))
            process_class = attrib.pop("backend")
            # Starting the threads
            process_obj = process_class.Manager(attrib, name=process)
            process_obj.start()
            self.pool.append(process_obj)
            message = "The thread [%s] was started!" % process
            print >> stdout, message
            log.info(message)
        # Start monitoring
        self.monitoring()

    def monitoring(self):
        """
        Will be look until all the threads die.
        """
        while True:
            try:
                still_alive = [ thread for pos, thread in enumerate(self.pool) if self.pool[pos].is_alive() ]
                if len(still_alive) == 0:
                    message = "All threads was closed!"
                    print >> stdout, message
                    log.info(message)
                    break
                sleep(settings.MANAGER_SLEEP)
            except:
                log.critical("Problem while monitoring the threads.")

    def finish(self, *args, **kwargs):
        """
        Will be called when used kill or ^C, so will die because the while in monitoring was broke,
           but we need guarantee that only will die when every script done 
        """
        # Finishing the threads
        while len([ thread for thread in self.pool if thread.is_alive() ]) > 0:
            for thread in self.pool:
                if thread.is_alive(): thread.join()
                message = "The thread [%s] was finished!" % thread.name
                print >> stdout, message
                log.info(message)
        message = "Finish instance."
        print >> stdout, message
        log.info(message)
