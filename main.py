import urllib3, yaml, cherrypy

#Define CherryPy Webservice
class FHIR_Facade_Server(object):
    @cherrypy.expose
    def index(self):
        return 'You are running FHIR-FACADE Version 0.0.1'

    @cherrypy.expose
    def fhir(self, request_string):
    # get content results from fhir server
        http = urllib3.PoolManager()
        contentResults = http.request('GET',SERVER_URL+':'+str(SERVER_PORT)+SERVER_BASE+request_string)
    # get consent results from fhir server based on patientIDs, casenr, studypseudonym
    #e.g. http://localhost:8080/fhir/Consent/?patient=patientID,casenr,studypseudonym
    #http://localhost:8080/fhir/Observation?code=http://testcode,_has:Patient:_has:Consent:status=true

    # traverse results and set bool flag per patient/record

    #return filtered results

        print(contentResults.data)
        return contentResults.data

if __name__ == '__main__':
    #Read config files
    with open('server_config.yml') as cfgfile:
        server_config = yaml.safe_load(cfgfile)

    with open('resource_config.yml') as cfgfile:
        resource_config = yaml.safe_load(cfgfile)

    #Set Up Global Variables
    FACADE_PORT = server_config['Facade']['Port']
    global SERVER_URL
    SERVER_URL = server_config['FHIR']['URL']
    global SERVER_PORT
    SERVER_PORT = server_config['FHIR']['Port']
    global SERVER_BASE
    SERVER_BASE = server_config['FHIR']['Base']



    # set up web server at FACADE_URL+FACADE_PORT
    facade_config = {'server.socket_port': FACADE_PORT}

    cherrypy.tree.mount(FHIR_Facade_Server())
    cherrypy.config.update(facade_config)

    cherrypy.engine.start()
    cherrypy.engine.block()