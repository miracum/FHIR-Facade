from flask import Flask
from flask_restful import Api
from resources.fhir_facade_server import FHIR_Facade_Server

app = Flask(__name__)
api = Api(app)

# set up web server at FACADE_URL+FACADE_PORT
api.add_resource(FHIR_Facade_Server, '/fhir/<string:resource>', '/fhir/<string:resource>/<string:search>')

