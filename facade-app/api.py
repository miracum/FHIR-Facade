import yaml, requests, os
from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
#from .resources.fhir_facade_server import FHIR_Facade_Server

app = Flask(__name__)
api = Api(app)

# Read config files

with open('./config/resource_config.yml') as cfgfile:
    resource_config = yaml.safe_load(cfgfile)

with open('./info.yml') as infofile:
    info = yaml.safe_load(infofile)

# Set up constants
# General
VERSION = info['Version']

# Network
RESOURCE_PATHS = resource_config['Resources']

#Define Webservice
def getConsentParams(type):
    consentParams = {}

    #Get parameter-paths defined in the resource_config.yml yaml file
    PATH_TO_PATIENT = RESOURCE_PATHS[type]['Subject']
    PATH_TO_DATE = RESOURCE_PATHS[type]['Date']

    #generate Consent-Query from params
    tempConsentQuery = {PATH_TO_PATIENT + ':_has:Consent:status': 'active'}

    return consentParams




    # get consent results from fhir server based on patientIDs, casenr, studypseudonym
    #e.g. http://localhost:8080/fhir/Consent/?patient=patientID,casenr,studypseudonym
    #http://localhost:8080/fhir/Observation?code=http://testcode,_has:Patient:_has:Consent:status=true

    # traverse results and set bool flag per patient/record

    #return filtered results

class FHIR_Facade_Server(Resource):

    def get(self, type):
        SERVER_URL = os.environ['FHIR_SERVER_URL']
        if(type == 'test'):
            s = requests.session()
            resp = s.get(SERVER_URL + "Patient?name=Tyron580")
            return resp.text

        if(type in resource_config['Resources']):
            s = requests.session()
            params = request.args.copy()
            params.update(getConsentParams(type))
            response = s.get(SERVER_URL + type, params=params)
            return response.json()
        else:
            s = requests.session()
            response = s.get(SERVER_URL + request.full_path[len('/fhir/'):-1])
            return response.json()

    def post(self, type, search='false'):
        SERVER_URL = os.environ['FHIR_SERVER_URL']
        if(search == '_search'):
            tempConsentQuery = getConsentParams(type)
            params = request.args.copy()

            if (type == 'test'):
                return request.args

            if (type in resource_config['Resources']):
                s = requests.session()

                params.update(tempConsentQuery)
                response = s.post(SERVER_URL + type, data=params)
                return response.json()
            else:
                s = requests.session()
                response = s.post(SERVER_URL + type, data=params)
                return response.json()
        else:
            return 'syntax error'

# set up web server at FACADE_URL+FACADE_PORT
api.add_resource(FHIR_Facade_Server, '/fhir/<string:type>', '/fhir/<string:type>/<string:search>')