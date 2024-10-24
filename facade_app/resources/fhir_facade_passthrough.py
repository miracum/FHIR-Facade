from resources.util.util_functions import get_passthrough_result
from flask import request, Response
from flask_restful import Resource


def passthrough_handle_request(self, is_post):
    params = request.args.copy()
    headers = dict(request.headers)
    data = bytes(request.data)

    if is_post:
        return get_passthrough_result(request.full_path, params, headers, data, True)
    else:
        return get_passthrough_result(request.full_path, params, headers, data, False)


class FHIR_Facade_Passthrough(Resource):

    def get(self):
        return passthrough_handle_request(self, False)

    def post(self):
        return passthrough_handle_request(self, True)
