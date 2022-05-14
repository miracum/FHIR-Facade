import yaml, requests, os, urllib.request
from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
from resources.fhir_facade_server import FHIR_Facade_Server

app = Flask(__name__)
api = Api(app)

# Read config file
with open(f'./info.yml') as infofile:
    info = yaml.safe_load(infofile)

VERSION = info['Version']

# set up web server at FACADE_URL+FACADE_PORT
api.add_resource(FHIR_Facade_Server, '/fhir/<string:type>', '/fhir/<string:type>/<string:search>')

if(__name__=='__main__'):
    app.run()
