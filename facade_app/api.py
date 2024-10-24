import os, yaml
from flask import Flask
from flask_restful import Api
from resources.fhir_facade_passthrough import FHIR_Facade_Passthrough
from resources.fhir_facade_server import FHIR_Facade_Server

temp = os.getenv("PASSTHROUGH_CONFIG", "")
if temp != "":
    pass_conf = yaml.safe_load(temp)
else:
    with open("../config/passthrough_config.yml") as cfgfile:
        pass_conf = yaml.safe_load(cfgfile.read())

app = Flask(__name__)
api = Api(app)

# set up web server at FACADE_URL+FACADE_PORT
api.add_resource(
    FHIR_Facade_Server,
    "/fhir/<string:resource>",
    "/fhir/<string:resource>/<string:search>",
)
if len(pass_conf["URLs"]) > 0:
    api.add_resource(FHIR_Facade_Passthrough, *pass_conf["URLs"])
