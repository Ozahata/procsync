from optparse import OptionParser
from os import getcwd, chdir
from os.path import join, exists
from pwd import getpwnam
from signal import signal, SIGINT, SIGTERM, SIGABRT
from sys import exit, stderr
from tempfile import gettempdir
try:
    from lockfile import FileLock
except:
    print >> stderr, "The application need the module lockfile to run.\nSee: http://pypi.python.org/pypi/lockfile"
    exit(1)
try:
    from daemon.daemon import DaemonContext
except:
    print >> stderr, "The application need the module daemon to run.\nSee: http://pypi.python.org/pypi/python-daemon"
    exit(1)

# First part get the option
parser = OptionParser(usage="Usage: %prog [options]", version="%prog 0.6", description="Synchronizer Stuffs Simple")

parser.add_option("-n", "--nofork", dest="is_nofork", action="store_true", help="Put the sync in single mode (Not put in background).", default=False)
parser.add_option("-p", "--path", dest="lock_file", metavar="path_and_file", help="Path and the name given to the lock file.")
parser.add_option("-c", "--configpath", dest="config_path", metavar="config_path", help="Path that where the config/settings/scripts will be get.")
parser.add_option("-u", "--user", dest="user_owner", metavar="name", help="Set the information to initial script.")

options, _ = parser.parse_args()

##########################
# Preparing the settings #
##########################
# Enter in the path that the person choose
if options.config_path: chdir(options.config_path)
# Now that we know the path, we can call the settings
from procsync.modules import logger as log
from procsync.modules import settings
from procsync.modules.thread.manager import ThreadManager

class SingleInstance():

    thread_manager = None

    def __init__(self, lock_file, uid, gid, is_nofork):
        lock = None
        self.thread_manager = ThreadManager()
        try:
            lock = FileLock(lock_file)
            self.thread_manager.lock = lock
            # Prepare to finish when receive a interrupt key/kill command
            if is_nofork:
                [ signal(signal_key, self.thread_manager.finish) for signal_key in [SIGTERM, SIGINT, SIGABRT] ]
                with lock:
                    self.thread_manager.start()
            else:
                context = DaemonContext(working_directory=getcwd(),
                               pidfile=lock,
                               uid=uid,
                               gid=gid,
                               files_preserve=log.handler_file,
                                # umask=0o002,
                                # Uncomment for direct command-line debugging
                                # stdout=sys.stdout,
                                # stderr=sys.stderr,
                               )
                context.signal_map = dict([ (signal_key, self.thread_manager.finish) for signal_key in [SIGTERM, SIGINT, SIGABRT] ])
                with context:
                    self.thread_manager.start()
        except Exception, e:
            log.exception("The instance generated a error, please check the Traceback [%s]." % e)
        finally:
            if lock is not None and lock.is_locked():
                log.info("Releasing the file lock")
                lock.release()

def main(options):
    try:
        # File that represent the lock
        lock_file = join(gettempdir(), settings.INSTANCE_NAME) if options.lock_file is None else options.lock_file
        # Information about the own user that will run the application (Used by Unix script)
        uid = gid = None
        if options.user_owner is not None:
            try:
                password_struct = getpwnam(options.user_owner)
                uid = password_struct.pw_uid
                gid = password_struct.pw_gid
            except Exception, e:
                log.warning("User name not found or have other problem [%s]!" % e)
                exit(1)
        # Test if the lock file exist
        if exists(lock_file + ".lock"):
            log.warning("Another instance is already running, or the program was interrupted.\nCheck if program already is running and if not, please delete the file [%s.lock]." % lock_file)
            exit(1)
        SingleInstance(lock_file, uid, gid, options.is_nofork)
    except Exception, e:
        print >> stderr, "Problem in runtime [%s]" % e

if __name__ == "__main__":
    main(options)
