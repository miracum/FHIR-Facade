import yaml, requests, os
from flask import Flask, request
from flask_restful import Resource

with open(f'../config/resource_config.yml') as cfgfile:
    resource_config = yaml.safe_load(cfgfile)

# Network
RESOURCE_PATHS = resource_config['Resources']

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

def getAllConsents(SERVER_URL):
    return [SERVER_URL]

class FHIR_Facade_Server(Resource):

    def get(self, resource):
        SERVER_URL = os.environ['FHIR_SERVER_URL']

        if(type in resource_config['Resources']):
            ALL_CONSENTS = getAllConsents(SERVER_URL)
            s = requests.session()
            params = request.args.copy()
            params.update(getConsentParams(resource))
            response = s.get(SERVER_URL + resource, params=params, headers=request.headers)
            return response.json()
        else:
            return f"The requested resource has not been configured. Please add the necessary configuration.\nOr if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly."

    def post(self, resource, search='false'):
        SERVER_URL = os.environ['FHIR_SERVER_URL']

        if(search == '_search'):
            tempConsentQuery = getConsentParams(resource)
            params = request.args.copy()

            if (resource in resource_config['Resources']):
                ALL_CONSENTS = getAllConsents(SERVER_URL)
                s = requests.session()

                params.update(tempConsentQuery)
                response = s.post(SERVER_URL + resource, data=params)
                return response.json()
            else:
                return f"The requested resource has not been configured. Please add the necessary configuration.\nOr if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly."
        else:
            return 'Syntax error. Use the appropriate fhir-post-search syntax: .../fhir/type/_search'