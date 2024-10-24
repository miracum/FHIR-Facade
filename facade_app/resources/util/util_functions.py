import os, requests, json
from requests.auth import HTTPBasicAuth


def get_passthrough_result(url, params, headers, data, is_post):
    SERVER_URL = os.getenv("FHIR_SERVER_URL", "")

    s = requests.sessions.Session()
    auth = HTTPBasicAuth(os.getenv("BA_USER_NAME", ""), os.getenv("BA_PASSWORD", ""))

    # Merge params and jsondata
    params["_format"] = "application/fhir+json"
    try:
        data = json.loads(data)
        data.update(params)
    except:
        data = {}
        data.update(params)

    headers.update(
        {
            "Accept": "application/fhir+json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )

    if is_post:
        response = s.post(
            SERVER_URL.replace("/fhir/", "") + url,
            auth=auth,
            headers=headers,
            params=data,
            verify=False,
        ).json()

    else:
        response = s.get(
            SERVER_URL.replace("/fhir/", "") + url,
            auth=auth,
            headers=headers,
            params=data,
            verify=False,
        ).json()

    return response
