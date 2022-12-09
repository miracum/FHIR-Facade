import yaml, json, requests, os, math
from requests.auth import HTTPBasicAuth
import uuid, shortuuid
from flask import request, Response
from flask_restful import Resource
from util.consentAndResourceUtil import getAllConsents, matchResourcesWithConsents
from util.bundleUtil import fhirBundlifyList
from util.pagingStoreController import storePage, getPage, clearPages


# import config from yml files
global resource_config
temp = os.getenv("RESOURCE_CONFIG", "")
if temp != "":
    resource_config = yaml.safe_load(temp)
else:
    with open("../config/resource_config.yml") as cfgfile:
        resource_config = yaml.safe_load(cfgfile)

RESOURCE_PATHS = resource_config["Resources"]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class FHIR_Facade_Server(Resource):
    def get(self, resource):

        # Health_Endpoint
        if resource == "healthZ":
            return Response(status=200)

        params = request.args.copy()
        SERVER_URL = os.environ["FHIR_SERVER_URL"]

        # Try loading config from request > env > file
        try:
            prov_conf = json.loads(params["provision_config"])
            if prov_conf == {} or not "coding" in prov_conf:
                raise Exception
        except:
            temp = os.getenv("PROVISION_CONFIG", "")
            if temp != "":
                prov_conf = json.loads(temp)
            else:
                with open("../config/general_provision_config.json") as cfgfile:
                    prov_conf = json.loads(cfgfile.read())
                print(
                    "no provision_config provided, defaulting to config/general_provision_config.json"
                )

        if resource == "Page" and "__page-id" in params:
            return getPage(params["__page-id"])

        if resource in RESOURCE_PATHS:
            # Check if resource has been configured properly
            if (
                RESOURCE_PATHS[resource]["Date"] == ""
                or RESOURCE_PATHS[resource]["Subject"] == ""
            ):
                return (
                    f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.",
                    403,
                )

            # refreshAllConsents
            all_consents = getAllConsents(SERVER_URL)
            page_size = int(os.environ["PAGE_SIZE"])
            int_page_size = int(os.getenv("INTERNAL_PAGE_SIZE", 2000))
            page_store_time = int(os.environ["PAGE_STORE_TIME"])
            raw_resources = []
            matched_resources = []
            page_id_list = []
            internal_page_id_list = []
            length_sum = 0

            # get initial resources from fhir server
            s = requests.session()
            auth = HTTPBasicAuth(
                os.getenv("BA_USER_NAME", ""), os.getenv("BA_PASSWORD", "")
            )

            response = s.get(
                SERVER_URL + resource,
                auth=auth,
                params=params,
                headers=request.headers,
                verify=False,
            ).json()
            if LOG_LEVEL == "DEBUG":
                print(f"initial response: {response}")
            if "entry" in response.keys():
                raw_resources = response["entry"]
                matched_resources = matchResourcesWithConsents(
                    resources=raw_resources,
                    consents=all_consents,
                    resource_config=RESOURCE_PATHS[resource],
                    provision_config=prov_conf,
                )

            # Iterate over potential paged responses
            while "next" in [link["relation"] for link in response["link"]]:

                # If there are to many resources matched, trigger internal paging
                if len(matched_resources) >= int_page_size:
                    uid = shortuuid.encode(uuid.uuid4())
                    storePage({"page": matched_resources[0:int_page_size]}, uid)
                    internal_page_id_list.append(uid)
                    length_sum += int_page_size
                    matched_resources = matched_resources[int_page_size:]

                link_index = [link["relation"] for link in response["link"]].index(
                    "next"
                )
                corrected_url = (
                    SERVER_URL + response["link"][link_index]["url"].split("/fhir/")[1]
                )

                response = s.get(corrected_url, auth=auth, verify=False).json()
                if LOG_LEVEL == "DEBUG":
                    print(f"paged response: {response}")

                # Extract entries and relevant fields
                raw_resources = response["entry"]

                matched_resources = matched_resources + matchResourcesWithConsents(
                    resources=raw_resources,
                    consents=all_consents,
                    resource_config=RESOURCE_PATHS[resource],
                    provision_config=prov_conf,
                )

            # Trigger internal paging for remaining Elements
            uid = shortuuid.encode(uuid.uuid4())
            storePage({"page": matched_resources}, uid)
            internal_page_id_list.append(uid)
            length_sum += len(matched_resources)

            # Page results and return first page
            num_of_pages = math.ceil(length_sum / page_size)
            next_page_id = ""
            matched_resources = getPage(internal_page_id_list.pop(), True)["page"]
            for i in range(num_of_pages):
                if i + 1 == num_of_pages:
                    topIndex = None
                    botIndex = i * page_size
                else:
                    topIndex = (i + 1) * page_size
                    botIndex = i * page_size

                if topIndex != None and topIndex >= len(matched_resources):
                    matched_resources.extend(
                        getPage(internal_page_id_list.pop(), True)["page"]
                    )

                curr_page, next_page_id = fhirBundlifyList(
                    list=matched_resources[botIndex:topIndex],
                    total=len(matched_resources),
                    uid=next_page_id,
                    page_size=page_size,
                    page_store_time=page_store_time,
                    facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                    lastPage=(i + 1 == num_of_pages),
                )
                page_id_list.append(curr_page["id"])

                storePage(curr_page, curr_page["id"], page_store_time)

            clearPages(page_store_time)

            if len(page_id_list) != 0:
                return getPage(page_id_list[0])
            else:
                emptySearchPage, nextUid = fhirBundlifyList(
                    list=[],
                    total=0,
                    page_size=page_size,
                    page_store_time=page_store_time,
                    facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                    lastPage=True,
                )
                storePage(emptySearchPage, emptySearchPage["id"], page_store_time)
                return emptySearchPage

        else:
            return (
                f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.",
                403,
            )

    def post(self, resource, search="false"):
        SERVER_URL = os.environ["FHIR_SERVER_URL"]

        if search == "_search":
            params = request.args.copy()

            if resource == "Page" and "__page-id" in params:
                return getPage(params["__page-id"])

            if resource in RESOURCE_PATHS:
                # Check if resource has been configured properly
                if (
                    RESOURCE_PATHS[resource]["Date"] == ""
                    or RESOURCE_PATHS[resource]["Subject"] == ""
                ):
                    return (
                        f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.",
                        403,
                    )

                # refreshAllConsents
                all_consents = getAllConsents(SERVER_URL)
                page_size = int(os.environ["PAGE_SIZE"])
                page_store_time = int(os.environ["PAGE_STORE_TIME"])
                int_page_size = int(os.getenv("INTERNAL_PAGE_SIZE", 2000))
                matched_resources = []
                raw_resources = []
                page_id_list = []
                internal_page_id_list = []
                length_sum = 0

                # get initial resources from fhir server
                s = requests.session()
                auth = HTTPBasicAuth(
                    os.getenv("BA_USER_NAME", ""), os.getenv("BA_PASSWORD", "")
                )

                # Merge params and jsondata
                try:
                    data = json.loads(request.data)
                    data.update(params)
                except:
                    data = {}
                    data.update(params)

                # Try loading config from request > env > file
                try:
                    prov_conf = json.loads(params["provision_config"])
                    if prov_conf == {} or not "coding" in prov_conf:
                        raise Exception
                except:
                    temp = os.getenv("PROVISION_CONFIG", "")
                    if temp != "":
                        prov_conf = json.loads(temp)
                    else:
                        with open("../config/general_provision_config.json") as cfgfile:
                            prov_conf = json.loads(cfgfile.read())
                        print(
                            "no provision_config provided, defaulting to config/general_provision_config.json"
                        )

                response = s.post(
                    SERVER_URL + resource + "/_search",
                    auth=auth,
                    params=data,
                    verify=False,
                ).json()
                if LOG_LEVEL == "DEBUG":
                    print(f"initial response: {response}")
                if "entry" in response.keys():
                    raw_resources = response["entry"]
                    matched_resources = matchResourcesWithConsents(
                        resources=raw_resources,
                        consents=all_consents,
                        resource_config=RESOURCE_PATHS[resource],
                        provision_config=prov_conf,
                    )

                # Iterate over potential paged responses
                while "next" in [link["relation"] for link in response["link"]]:

                    # If there are to many resources matched, trigger internal paging
                    if len(matched_resources) >= int_page_size:
                        uid = shortuuid.encode(uuid.uuid4())
                        storePage({"page": matched_resources[0:int_page_size]}, uid)
                        internal_page_id_list.append(uid)
                        length_sum += int_page_size
                        matched_resources = matched_resources[int_page_size:]

                    link_index = [link["relation"] for link in response["link"]].index(
                        "next"
                    )
                    corrected_url = (
                        SERVER_URL
                        + response["link"][link_index]["url"].split("/fhir/")[1]
                    )

                    response = s.get(corrected_url, auth=auth, verify=False).json()
                    if LOG_LEVEL == "DEBUG":
                        print(f"paged response: {response}")

                    # Extract entries and relevant fields
                    raw_resources = response["entry"]

                    matched_resources = matched_resources + matchResourcesWithConsents(
                        resources=raw_resources,
                        consents=all_consents,
                        resource_config=RESOURCE_PATHS[resource],
                        provision_config=prov_conf,
                    )

                # Trigger internal paging for remaining Elements
                uid = shortuuid.encode(uuid.uuid4())
                storePage({"page": matched_resources}, uid)
                internal_page_id_list.append(uid)
                length_sum += len(matched_resources)

                # Page results and return first page
                num_of_pages = math.ceil(length_sum / page_size)
                next_page_id = ""
                matched_resources = getPage(internal_page_id_list.pop(), True)["page"]
                for i in range(num_of_pages):
                    if i + 1 == num_of_pages:
                        topIndex = None
                        botIndex = i * page_size
                    else:
                        topIndex = (i + 1) * page_size
                        botIndex = i * page_size

                    if topIndex != None and topIndex >= len(matched_resources):
                        matched_resources.extend(
                            getPage(internal_page_id_list.pop(), True)["page"]
                        )

                    curr_page, next_page_id = fhirBundlifyList(
                        list=matched_resources[botIndex:topIndex],
                        total=len(matched_resources),
                        uid=next_page_id,
                        page_size=page_size,
                        page_store_time=page_store_time,
                        facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                        lastPage=(i + 1 == num_of_pages),
                    )
                    page_id_list.append(curr_page["id"])

                    storePage(curr_page, curr_page["id"], page_store_time)

                clearPages(page_store_time)

                if len(page_id_list) != 0:
                    return getPage(page_id_list[0])
                else:
                    emptySearchPage, nextUid = fhirBundlifyList(
                        list=[],
                        total=0,
                        page_size=page_size,
                        page_store_time=page_store_time,
                        facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                        lastPage=True,
                    )
                    storePage(emptySearchPage, emptySearchPage["id"], page_store_time)
                    return emptySearchPage

            else:
                return (
                    f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.",
                    403,
                )
        else:
            return "Syntax error. Use the appropriate fhir-post-search syntax: .../fhir/type/_search"
