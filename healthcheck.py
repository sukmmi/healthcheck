import json
import socket
from datetime import datetime
import os
import logging


logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger('healthcheck')

def webAppAvailability(name):
    status={}
    status['name']=name
    status['measure_type']="Availability"
    status['measure_value']="False"
    status['timestamp']=""
    status['errormessage']="Internal Server Error 500"
    return status

def getHostName():
    if socket.gethostname().find('.')>=0:
        name=socket.gethostname()
    else:
        name=socket.gethostbyaddr(socket.gethostname())[0]
    return name

def configValid(configFile):
        log = logging.getLogger('configValid')
        CONFIG_LEVEL1_MUST_KEYS=['env']
        CONFIG_LEVEL2_MUST_KEYS=['applications']
        CONFIG_LEVEL3_MUST_KEYS=['protocol','hosts','port','user','password','apps','type','enabled']
        CONFIG_KEY_FOUND=[]
        INVALID_CONFIG_FILE=False
        FOUND_ENV=False
        FOUND_APPLICATIONS=False

        if os.path.exists(configFile):

                try:
                      log.info("Validating configuration file %s" % (configFile))
                      with open(configFile) as f:
                          config = json.load(f)

                      for config_env in config.keys(): #Iterate environments in configuration file
                             """
                             In TOP section
                             """

                             if config_env in CONFIG_LEVEL1_MUST_KEYS and not FOUND_ENV :
                                   FOUND_ENV=True
                                   for config_env_item in config[config_env]: #Iterate Environment attributes
                                         """
                                         In TOP > env
                                         """
                                         log.info("Checking settings for Environment: %s  Level: %s" % (config_env_item['name'],config_env_item['level']))
                                         FOUND_SETTINGS=False
                                         for config_env_key in config_env_item:
                                                """
                                                In TOP > env > 'environment name'
                                                """

                                                if config_env_key in CONFIG_LEVEL2_MUST_KEYS and not FOUND_APPLICATIONS: #Look for 'SETTINGS' key
                                                      """
                                                      In TOP > env > 'environment name' > Settings
                                                      """
                                                      FOUND_APPLICATIONS=True #Key found
                                                      log.debug("Environment Key Name %s" % (config_env_key))
                                                      for config_env_applications_key in config_env_item[config_env_key]:
                                                            """
                                                            In TOP > env > 'environment name' > Applications > values'
                                                            """
                                                            log.debug("Application %s" % (config_env_applications_key))

                                                            """
                                                            Check if 'must' keys exist in settings - if not then break
                                                            """
                                                            for key in config_env_applications_key: #Iterate each key in settings
                                                                  if key in CONFIG_LEVEL3_MUST_KEYS:
                                                                        CONFIG_KEY_FOUND.append(key)

                                                            log.debug("Number of keys found %d" % (len(CONFIG_KEY_FOUND)))

                                                            """
                                                            if atleast one 'must' keys not found then break from the loop
                                                            and declare configuration file as invalid
                                                            """
                                                            if not (len(CONFIG_KEY_FOUND) == len(CONFIG_LEVEL3_MUST_KEYS)):
                                                                  INVALID_CONFIG_FILE=True
                                                                  break

                                                            CONFIG_KEY_FOUND=[]

                                                else:
                                                      continue
                                         if INVALID_CONFIG_FILE:
                                               log.info("Failed to validate Environment: %s  Level: %s " % (config_env_item['name'],config_env_item['level']))
                                         else:
                                               log.info("Successfully validated Environment: %s  Level: %s " % (config_env_item['name'],config_env_item['level']))
                                   break
                             else:
                                   continue

                except Exception,e:
                       INVALID_CONFIG_FILE=True
                       log.error('Something went wrong while reading web configuration json file %s' % (configFile))
                       log.error(e,exc_info=True)
        else:
            log.error("Configuration File %s does not exist" % (configFile))

        if INVALID_CONFIG_FILE:
              log.info("Configuration File check Failed")
              return False
        else:
              log.info("Configuration File check Passed")
              return True

class HealthCheckApplication(object):
    def __init__(self,environment,level,name,type,host,port,protocol):
        self.type=type
        self.environment=environment
        self.level=environment
        self.name=name
        self.protocol=protocol
        self.host=host
        self.port=port
        self.timeoutseconds=30

class HealthCheckStatus(object):
    def __init__(self,host,application,application_type,type,value,timestamp,message,errormessage):
        self.application=application
        self.application_type=application_type
        self.type=type
        self.value=value
        self.message=message
        self.errormessage=errormessage
        self.timestamp=timestamp
        self.host=host

    def asDict(self):
        _dict_status={}
        _dict_status["host"]=self.host
        _dict_status["application_type"]=self.application_type
        _dict_status["application"]=self.application
        _dict_status["type"]=self.type
        _dict_status["value"]=self.value
        _dict_status["message"]=self.message
        _dict_status["errormessage"]=self.message
        return _dict_status

class HealthCheckConfig(object):

    def __init__(self,configFile):
        log = logging.getLogger('HealthCheckConfig')
        self.configFilename=configFile
        self.applications=[]
        if configValid(configFile):
            with open(configFile) as f:
                config_data=json.load(f)
                self.initialize(config_data)
        else:
            log.info("Stop executing as Configuration File %s is invalid" % (configFile))

    def initialize(self,config):
        log = logging.getLogger('HealthCheckConfig.initialize')
        for config_key in config:
            if config_key == 'env':
                for environment in config[config_key]:
                    for environment_key in environment:
                        if environment['enabled'].upper() == 'YES': #Check if Environment check is enabled in Configuraiton file
                            if environment_key == 'applications':
                                for application in environment[environment_key]:
                                    if application["enabled"].upper() == 'YES': #Check if Application check is enabled in Configuraiton file
                                        for name in application['apps']:
                                            if application['hosts'] and isinstance(application['hosts'], list):
                                                for host in application['hosts']:
                                                    self.applications.append(HealthCheckApplication(environment['name'],
                                                                             environment['level'],
                                                                             name,
                                                                             application['type'],
                                                                             host,
                                                                             application['port'],
                                                                             application['protocol']
                                                                             ))
                                            else:
                                                self.applications.append(HealthCheckApplication(environment['name'],
                                                                         environment['level'],
                                                                         name,
                                                                         application['type'],
                                                                         application['hosts'],
                                                                         application['port'],
                                                                         application['protocol']
                                                                         ))
                                    else:
                                        log.info("%s is disabled" %(application["Description"]))

class Healthcheck(object):
        def __init__(self,configFile):
            self.status_dict={}
            self.status_dict["hostname"]=getHostName()
            self.status_dict["timestamp"]=str(datetime.now())
            self.status_dict["output"]=[]
            self.status_output=[]
            self.hc_config=HealthCheckConfig(configFile)


        def getStatus(self):
            log = logging.getLogger('Healthcheck.getStatus')
            status_output=[]
            if self.hc_config.applications:
                for application in self.hc_config.applications:
                    if application.type.upper() == 'WEBAPP':
                        self.status_dict["output"].append(HealthCheckStatus(application.host,application.name,application.type,'Availability','True','20170523','Success','200 OK').asDict())
                    elif application.type.upper() == 'DISK':
                        self.status_dict["output"].append(HealthCheckStatus(application.host,application.name,application.type,'Availability','True','20170523','Success','Responding').asDict())
                    else:
                        log.info("Invalid Application Type")
            else:
                log.info("No applications loaded")

        def save(self,filename):
            log = logging.getLogger('Healthcheck.save')
            if not self.status_dict:
                log.info(json.dumps(self.status_dict,indent=4))
                log.info('Saving to File %s' % (filename))


hc = Healthcheck(os.path.abspath('config.json'))
hc.getStatus()
hc.save('f')


#hc.display()
#hc.status('WebApp')
#hc.display()
