import logging
import json
import os
import sys

DEFAUTL_LOGGING_LEVEL=logging.INFO

def initializeLogging(configfile=None,default_level=logging.INFO,filename=None):
    if configfile:
        try:
            with open(configfile) as f:
                config=json.load(f)
                for config_key in config.keys():
                    if 'VERBOSE' == config_key.upper():
                        if 'YES' == config[config_key].upper():
                            default_level=logging.DEBUG
                        elif 'NO' == config[config_key].upper():
                            default_level=logging.INFO
                    if 'LOG' == config_key.upper():
                        filename = config[config_key]
        except IOError as ioerr:
            sys.stderr.write("Unable to initialize logging..Exit"+'\n')
            sys.stderr.write(str(ioerr)+'\n')
            sys.exit(1)
        except Exception as err:
            sys.stderr.write("Following exception occurred while reading config file\n")
            sys.stderr.write(str(err)+'\n')
            sys.stderr.write("Unable to initialize logging..Exit"+'\n')
            sys.exit(1)

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if not filename == None:
        try:
            #Ensure log file is valid and writable
            createLogFile(filename)
            logging.basicConfig(filename=filename,level=default_level,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        except (IOError, OSError) as e:
            logging.basicConfig(level=default_level,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            log.error(e)
            log.error("System Exit with status code 2")
            sys.exit(2)
    else:
        logging.basicConfig(level=default_level,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def createLogFile(logfile):
    try:
        if os.path.isfile(logfile):
            if os.access(logfile, os.W_OK):
                sys.stdout.write('Log file %s \n' % logfile)
            else:
                sys.stderr.write('Write access to log %s denied\n' % logfile)
                sys.stderr.write('Exit\n')
                sys.stderr.write("System Exit with status code 2")
                sys.exit(2)
        else:
            if not os.path.isdir(logfile):
                if os.path.isdir(os.path.dirname(os.path.abspath(logfile))):
                    sys.stdout.write('Writing to log file %s \n' % logfile)
                    #touch file
                    with open(logfile, 'a'):
                        os.utime(logfile, None)
                else:
                    sys.stderr.write('Log directory %s do not exist\n' % os.path.dirname(os.path.abspath(logfile)))
            else:
                sys.stderr.write('Invalid log %s\n' % logfile)
                sys.stderr.write("System Exit with status code 2")
                sys.exit(2)

    except (IOError, OSError) as e:
        sys.stderr.write("Following exception occurred while reading config file\n")
        sys.stderr.write(str(e)+'\n')
        sys.stderr.write("System Exit with status code 2")
        sys.exit(2)

def consoleLogging(filename=None):
    if filename:
        initializeLogging(filename='console.log',default_level=DEFAUTL_LOGGING_LEVEL)
    else:
        initializeLogging(default_level=DEFAUTL_LOGGING_LEVEL)

if __name__ == '__main__':
    initializeLogging(default_level=DEFAUTL_LOGGING_LEVEL)
