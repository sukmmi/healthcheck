#std libs
import logging
import json
import os
import sys
import datetime
import re

from service import Service
#project

#Option name where list of services will be defined
CONFIG_CHECKS_LIST_OPTION='checks'
CONFIG_GOLDEN_OPTIONS=['log', CONFIG_CHECKS_LIST_OPTION]
CONFIG_EMAIL_OPTIONS=['smtp','email_enabled','email_subject']
CONFIG_OTHER_OPTIONS=['env_name',
                      'env_level',
                      'alert_lifetime',
                      'verbose',
                      'version',
                      'comment',
                      'report_type'
                      ]

#Options in this list will be kept and rest discarded
CONFIG_ALL_OPTIONS=CONFIG_GOLDEN_OPTIONS + CONFIG_EMAIL_OPTIONS + CONFIG_OTHER_OPTIONS

CONFIG_SERVICES_GOLDEN_OPTIONS=['type','service','protocol','hosts','port','user','password']
CONFIG_SERVICES_OTHER_OPTIONS=['enabled','debug','description','ignored_services']
CONFIG_SERVICES_TYPE_VALID_VALUES=['webapp','disk','sas.servers']

#Options in this list will be kept and rest discarded
CONFIG_SERVICES_ALL_OPTIONS= CONFIG_SERVICES_GOLDEN_OPTIONS + CONFIG_SERVICES_OTHER_OPTIONS

class HealthCheckConfig(object):

    def __init__(self,configfile,configcheck=False):
        self.configfile=configfile
        self.services=[]
        self.checkonly=configcheck
        self.logfile='logfile.log'
        self.enabled=False
        self.smtp_host='unknown'
        self.smtp_port=25
        self.smtp_user='unknown'
        self.smpt_password=''
        self.smtp_sender='unknown'
        self.smtp_receiver=[]
        self.env_name=""
        self.env_level='unknown'
        self.interval=0
        self.frequency=0
        self.valid=False
        self.email_enabled=False
        self.email_subject='Email from HealthCheck'
        self.alert_lifetime=2*60*60 # 2 hours
        self.jinja2_template='status.html.template'
        self.full_health_report_enabled=False
        self.full_health_report_schedule=[]
        self.logging_level=logging.INFO
        self.ssh_id_rsa_filename='~/.ssh/id_rsa'
        self.run_as_service=True
        #Valid values ALL and ALERT
        self.report_type="ALERT"
        self.load()


    def load(self):
        log = logging.getLogger('config.load()')

        if self.checkonly:
            log.info("Configuration check only")

        self.valid=self.validate(self.configfile)

        if self.valid:
            try:
                with open(self.configfile) as f:
                    config=json.load(f)

                #Set top level properties
                for config_key in config:
                    if config_key in CONFIG_ALL_OPTIONS:
                        log.debug("Got %s:%s" % (config_key.upper(),config[config_key]))
                        if 'ENV_NAME' == config_key.upper():
                            self.env_name= config[config_key]
                        elif 'LOG' == config_key.upper():
                            self.logfile= config[config_key]
                        elif 'VERBOSE' == config_key.upper():
                            if 'YES' == config[config_key].upper():
                                self.logging_level=logging.DEBUG
                            else:
                                self.logging_level=logging.INFO
                        elif 'ALERT_LIFETIME' == config_key.upper():
                            self.alert_lifetime= config[config_key]
                        elif 'REPORT_TYPE' == config_key.upper():
                            if config[config_key].upper() in ['ALL','ALERT']:
                                if 'ALL' == config[config_key].upper():
                                    self.report_type= config[config_key]
                                elif 'HTML' == config[config_key].upper():
                                    self.report_type= config[config_key]
                            else:
                                log.debug("Valid value for report_type is ALL|ALERT|HTML")
                        elif 'SMTP' == config_key.upper():
                            for smtp_key in config[config_key]:
                                if 'HOST' == smtp_key.upper():
                                    self.smtp_host = config[config_key][smtp_key]
                                if 'PORT' == smtp_key.upper():
                                    self.smtp_port = config[config_key][smtp_key]
                                if 'USER' == smtp_key.upper():
                                    self.smtp_user = config[config_key][smtp_key]
                                if 'PASSWORD' == smtp_key.upper():
                                    self.smtp_password = config[config_key][smtp_key]
                                if 'SENDER' == smtp_key.upper():
                                    self.smtp_sender = config[config_key][smtp_key]
                                if 'RECEIVER' == smtp_key.upper():
                                    self.smtp_receiver = config[config_key][smtp_key]
                        elif 'ENABLED' == config_key.upper():
                            if 'YES' == config_key.upper():
                                self.enabled=True
                        elif 'EMAIL_ENABLED' == config_key.upper():
                            if 'YES' == config[config_key].upper():
                                log.debug("email feature enabled")
                                self.email_enabled=True
                        elif 'EMAIL_SUBJECT' == config_key.upper():
                            self.email_subject=config[config_key]

                #Find service and create service class instance
                for services in config[CONFIG_CHECKS_LIST_OPTION]:

                    service_upper_case=[]
                    for k in services:
                        service_upper_case.append(k.upper())

                    #for service_upcase_property in service_upper_case:
                        #log.debug("upper case service properties %s " % service_upcase_property)

                    if "ENABLED" in service_upper_case:
                        if "NO" == services["enabled"].upper():
                            service_enabled=False
                        else:
                            service_enabled=True
                    else:
                        service_enabled=True

                    if "SSH_ID_RSA_FILENAME" in service_upper_case:
                        ssh_id_rsa_filename=services["ssh_id_rsa_filename"]
                        log.debug("Set non-default ssh private key  %s" % ssh_id_rsa_filename)
                    else:
                        ssh_id_rsa_filename=''

                    if "DEBUG" in service_upper_case:
                        if "YES" == services["debug"].upper():
                            debug=True
                        else:
                            debug=False
                            log.debug("debug is set to yes")
                    else:
                        debug=False

                    if "ENVIRONMENT" in service_upper_case:
                        environment_name=services["environment"]
                    else:
                        environment_name="unknown"

                    if "LEVEL" in service_upper_case:
                        environment_level=services["level"]
                    else:
                        environment_level="unknown"

                    if "GROUP" in service_upper_case:
                        group=services["group"]
                    else:
                        group="Others"

                    if "IGNORED_SERVICES" in service_upper_case:
                        ignored_services=services["ignored_services"]
                    else:
                        ignored_services=[]

                    if  service_enabled and services['type'] in CONFIG_SERVICES_TYPE_VALID_VALUES:
                        log.debug("Loading services from Configuration file")
                        for service in services['service']:
                            if service not in ignored_services:
                                self.services.append(Service(environment_name,
                                                             environment_level,
                                                             group,
                                                             service,
                                                             services['type'],
                                                             services['hosts'],
                                                             services['port'],
                                                             services['protocol'],
                                                             services['user'],
                                                             services['password'],
                                                             ignored_services,
                                                             debug=debug,
                                                             ssh_private_key_filename=ssh_id_rsa_filename
                                                             )
                                                     )
                                log.debug("Added Service %s to check" % service)
                            else:
                                log.debug("Service %s found in ignore list %s" % (service,ignored_services))
                                log.debug("Service %s ignored" % service)

                    else:
                        log.debug("Removed Service %s from check" % services)

            except (IOError, OSError) as e:
                log.error("Exception occurred while loading config file")
                log.error(e)
                #log.error("System Exit with status code 2")
                #sys.exit(2)
        else:
            log.error("Unable to load configuration file because either it does not exist or is invalid")
            #log.error("System Exit with status code 2")
            #sys.exit(2)



    def setLogOptions(self,config):
        for config_key in config.keys():
            if 'VERBOSE' == config_key.upper():
                if 'YES' == config[config_key].upper():
                    self.logging_level=logging.DEBUG
            elif 'LOG' == config_key.upper():
                self.logfile= config[config_key]

    def isValid(self):
        #return self.validate(self.configfile)
        return self.valid



    def validate(self,configfile):
        log = logging.getLogger('config.HealthCheckConfig.validate()')
        VALID_CONFIG_FILE=True
        #CONFIG_GOLDEN_OPTIONS=['log','services']
        #CONFIG_SERVICES_GOLDEN_OPTIONS=['type','service','protocol','hosts','port','user','password']

        log.debug("Validating configuration File Exist %s?" % (configfile))
        if os.path.exists(configfile):
                try:
                    with open(configfile) as f:
                        config = json.load(f)
                    log.debug(json.dumps(config,indent=4))
                    #check golden keys
                    CONFIG_OPTIONS=[]
                    for golden_key in CONFIG_GOLDEN_OPTIONS:
                        if not golden_key in config:
                            log.debug("Property %s is missing in config file" % golden_key)
                            VALID_CONFIG_FILE=False
                            #return False

                    if not VALID_CONFIG_FILE:
                        log.debug("Configuration check Failed")
                        return False
                    else:
                        log.debug("Config Golden keys passed")

                    for service_item in config[CONFIG_CHECKS_LIST_OPTION]:
                        for service_golden_key in CONFIG_SERVICES_GOLDEN_OPTIONS:
                            if not service_golden_key in service_item:
                                log.debug('key:value \"%s:value\" is missing for service %s' % (service_golden_key,service_item))
                                VALID_CONFIG_FILE=False

                    if not VALID_CONFIG_FILE:
                        log.debug("Configuration check Failed")
                        return False
                    else:
                        log.debug("Config Golden Service keys present")
                    config={}
                    log.debug("Configuration file is valid")
                    return True

                except Exception,e:
                       log.error('Exception occurred while loading configuration json file %s' % (configfile))
                       log.error(e,exc_info=True)
        else:
            log.error("Configuration File %s does not exist" % configfile)
            return False

def maindir():
    LIB_DIR = os.path.dirname(os.path.realpath(__file__))
    PARENT_OF_LIB_DIR=os.path.abspath(os.path.join(LIB_DIR, os.pardir))
    return PARENT_OF_LIB_DIR

def configddir():
    CONFIGD_DIR=os.path.join(maindir(), 'conf.d')
    return CONFIGD_DIR

def datadir():
    DATA_DIR=os.path.join(maindir(), 'data')
    return DATA_DIR

def logsdir():
    LOGS_DIR=os.path.join(maindir(), 'logs')
    return LOGS_DIR

def datapath():
    DATA_PKL=os.path.join(datadir(), 'alerts.dat')
    return DATA_PKL

def defaultconfigpath():
    DEFAULT_CONFIG_FILE = os.path.join(configddir(),'default.cfg')
    return DEFAULT_CONFIG_FILE

def defaultlogpath():
    DEFAULT_LOG_FILE = os.path.join(logsdir(),'sashealthcheck_default.log')
    return DEFAULT_LOG_FILE

def getconfigpath():
    DEFAULT_CONFIG_FILE=defaultconfigpath()
    HC_CONFIG_FILE=os.getenv('HC_CONFIG_FILE',DEFAULT_CONFIG_FILE)
    #in case HC_CONFIG_FILE is set and empty
    if not HC_CONFIG_FILE:
        HC_CONFIG_FILE=DEFAULT_CONFIG_FILE
    return HC_CONFIG_FILE

def getconfigname():
    #Get configuration file name without . extension
    format_pat= re.compile(
                            r'(?:(?:.+\/)(?P<config_filename>(.+?))(?:\.(.+)|$))?'
                      )
    match_dict = format_pat.match(getconfigpath())
    if match_dict:
        match_output=dict(match_dict.groupdict())
        DEFAULT_CONFIG_NAME=match_output['config_filename']
    else:
        DEFAULT_CONFIG_NAME="config_default"
    return DEFAULT_CONFIG_NAME

def getpiddir():
    piddir=maindir()
    return piddir

def getpidname():
    pidname=getconfigname()
    return pidname

def gethtmltemplatedir():
    HTML_TEMPLATE_PATH = os.path.join(maindir(),'html')
    return HTML_TEMPLATE_PATH
