#! /usr/bin/python2.7

import sys                      #variables/functions that interact strongly with the interpreter
import os                       #various functions related to the OS (path, pid...)
import tempfile                 #to get temp dir
import logging
import signal
import inspect                  #for debug info
import pwd       
         
import loghelper
import syncfolders

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

import yaml                     #parse/write yaml

class SigTermException(Exception): 
    pass

class GracefulDeath:
    """Catch signals to allow graceful shutdown."""

    def __init__(self):
        self.last_signal=-1
        self.received_signal = self.received_term_signal = False
        self.last_frame=None
        catch_signals = [
            1,
            2,
            3,
            10,
            12,
            15,
        ]
        for signum in catch_signals:
            signal.signal(signum, self.handler)

    def handler(self, signum, frame):
        self.last_signal = signum
        self.last_frame = frame
        self.received_signal = True
        if signum in [2, 3, 15]:
            self.received_term_signal = True
            filename, line_number, clsname, code, index=inspect.getframeinfo(frame)
            raise SigTermException(('Received signal %s on line %s in function %s from %s : %s' % (str(self.last_signal),str(line_number),clsname,filename,code)))
            
def main(config):
    sighandler = GracefulDeath()

    ##
    ## Set logging facility
    ##
    loglevels = {'info': logging.INFO, 'debug': logging.DEBUG,
                     'error': logging.ERROR, 'warning': logging.WARNING}

    log_format = '%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s'
    formatter = loghelper.MultilineFormatter(log_format)

    rootlogger = logging.getLogger()
    rootlogger.setLevel(loglevels[config["logs"]["log_level"]])

    script_log=os.path.join(config["logs"]["log_directory"],"syncFolders.log")
    file_handler = logging.handlers.RotatingFileHandler(script_log, maxBytes=(1048576*config["logs"]["log_max_size"]), backupCount=config["logs"]["log_max_backup"])
    file_handler.setFormatter(formatter)
    rootlogger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    rootlogger.addHandler(stream_handler)

    logger = logging.getLogger(__name__)
    tabbed_logger = loghelper.TabbedAdapter(logger, {})

    tabbed_logger.info("Starting Script",tab=0)


    ## Check/Set lockfile
    lock_file=os.path.join(tempfile.gettempdir(),"syncFolders.pid")


    # Check if lock file exists, or create it
    if os.path.isfile(lock_file):
        tabbed_logger.info("Script is already running, aborting.")
        sys.exit()
        
    file(lock_file, 'w').write(str(os.getpid()))

    #delete old archive files
    loghelper.purge_logs(config["logs"]["archive_directory"])
        
    had_errors=False

    for folder_config in config["folders"]:
        try:
            syncfolders.sync_folder(folder_config,config["notifications"],config["logs"]["log_directory"],config["logs"]["archive_directory"])
        except SigTermException as e:
            tabbed_logger.warning("Script as received a termination signal")
            tabbed_logger.warning(e)
            had_errors=True
            break
        except (Exception) as e:
            tabbed_logger.warning("Something happened during this sync")
            tabbed_logger.warning(e)
            had_errors=True
            raise

    os.remove(lock_file)
    rc=0
    if had_errors:
        tabbed_logger.info("Synchro completed with errors")
        rc=1
    else:
        tabbed_logger.info("Synchro completed")

    tabbed_logger.info("------------------------------------------------")
    return rc

if __name__ == "__main__":
    #get current user
    current_user=pwd.getpwuid(os.getuid()).pw_name
                
    ## Load configuration file
    script_directory=os.path.dirname(os.path.realpath(__file__))
    config_file_yaml=os.path.join(script_directory, 'config.yaml')

    if os.path.isfile(config_file_yaml)==False:
        print("Configuration file doesn't exists")
        sys.exit(10)
        
    with open(config_file_yaml, 'r') as f:
        config = yaml.load(f,Loader=yaml.Loader)


    # Create logs directory if they don't exist
    if not os.path.isdir(config["logs"]["log_directory"]):
        print("Create log directory")
        try:
            os.makedirs(config["logs"]["log_directory"])
        except OSError as e:
            print("Cannot create log directory %s" % config["logs"]["log_directory"])
            print("Check if the current user (%s) is allowed to create this directory." % current_user)
            print(e)
            sys.exit(11)
        except (Exception) as e:
            print("Cannot create log directory %s" % config["logs"]["log_directory"])
            raise
        

    if not os.path.isdir(config["logs"]["archive_directory"]):
        print("Create archives directory")
        try:
            os.makedirs(config["logs"]["archive_directory"])
        except OSError as e:
            print("Cannot create archive directory %s" % config["logs"]["archive_directory"])
            print("Check if the current user (%s) is allowed to create this directory." % current_user)
            print(e)
            sys.exit(11)
        except (Exception) as e:
            print("Cannot create archive directory %s" % config["logs"]["archive_directory"])
            raise
            
    rc=main(config)
    
    exit(rc)

