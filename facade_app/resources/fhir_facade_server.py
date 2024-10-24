import yaml, json, requests, os, math, time, multiprocessing, logging
from requests.auth import HTTPBasicAuth
from functools import partial
from resources.fhir_facade_passthrough import passthrough_handle_request
import uuid, shortuuid
import flask
from flask import request, Response
from flask_restful import Resource
from util.consentAndResourceUtil import getAllConsents, matchResourcesWithConsents
from util.bundleUtil import fhirBundlifyList
from util.pagingStoreController import (
    storePage,
    getPage,
    clearPages,
    storeConsents,
    loadConsents,
)

# import config from yml files
temp = os.getenv("RESOURCE_CONFIG", "")
if temp != "":
    resource_config = yaml.safe_load(temp)
else:
    with open("../config/resource_config.yml") as cfgfile:
        resource_config = yaml.safe_load(cfgfile)

temp = os.getenv("PASSTHROUGH_CONFIG", "")
if temp != "":
    pass_config = yaml.safe_load(temp)
else:
    with open("../config/passthrough_config.yml") as cfgfile:
        pass_config = yaml.safe_load(cfgfile)

PASS_RESOURCES = pass_config["Resources"]
RESOURCE_PATHS = resource_config["Resources"]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

if LOG_LEVEL == "DEBUG":
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(multiprocessing.SUBDEBUG)


def handleRequest(self, resource, search=""):

    # create mutable request.args copy
    params = request.args.copy()

    # Health_Endpoint
    if resource == "healthZ":
        return Response(status=200)

    # Paging request
    if resource == "Page" and "__page-id" in params:
        return getPage(params["__page-id"])

    if resource in PASS_RESOURCES:
        return passthrough_handle_request(self, False)

    # Return error code if request is invalid
    if search != "_search":
        return "Syntax error. Use the appropriate fhir-post-search syntax: .../fhir/type/_search"

    # Check if resource has been configured
    if resource not in RESOURCE_PATHS:
        return (
            f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.",
            403,
        )

    # Check if resource has been configured properly
    if (
        RESOURCE_PATHS[resource]["Date"] == ""
        or RESOURCE_PATHS[resource]["Subject"] == ""
    ):
        return (
            f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.",
            403,
        )

    # Initialize environment variables
    SERVER_URL = os.getenv("FHIR_SERVER_URL", "")
    PAGE_SIZE = int(os.environ["PAGE_SIZE"])
    PAGE_STORE_TIME = int(os.environ["PAGE_STORE_TIME"])
    INT_PAGE_SIZE = int(os.getenv("INTERNAL_PAGE_SIZE", 2000))
    CONSENT_CACHE_TIME = int(os.getenv("CONSENT_CACHE_TIME", 60))
    PROCESSES_PER_WORKER = int(os.getenv("PROCESSES_PER_WORKER", 1))
    MP_CHUNK_SIZE = int(os.getenv("MP_CHUNK_SIZE", 50))

    # Initialize multiprocessing pool with specified number of processes
    mp = multiprocessing.get_context("spawn")
    with mp.Pool(PROCESSES_PER_WORKER) as pool:

        matched_resources = []
        raw_resources = []
        page_id_list = []
        internal_page_id_list = []
        length_sum = 0

        params["_format"] = "application/fhir+json"
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # refreshAllConsents
        [all_consents, timeStamp] = loadConsents()
        if (timeStamp + CONSENT_CACHE_TIME) < time.time() or len(all_consents) == 0:
            all_consents = getAllConsents(SERVER_URL)
            storeConsents([all_consents, time.time()])

            if LOG_LEVEL == "INFO":
                print(f"refreshed consents at {int(time.time())}seconds")
        if LOG_LEVEL == "DEBUG":
            print(f"all consents: {all_consents}")

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
            headers=headers,
            params=data,
            verify=False,
        ).json()
        if LOG_LEVEL == "DEBUG":
            print(f"initial response: {response}")
        if "entry" in response.keys():
            raw_resources = response["entry"]
            mapped_results = pool.map(
                partial(
                    matchResourcesWithConsents,
                    consents=all_consents,
                    resource_config=RESOURCE_PATHS[resource],
                    provision_config=prov_conf,
                ),
                raw_resources,
                chunksize=MP_CHUNK_SIZE,
            )
            for result in mapped_results:
                matched_resources.extend(result)

        # Iterate over potential paged responses
        while "next" in [link["relation"] for link in response["link"]]:

            # If there are to many resources matched, trigger internal paging
            if len(matched_resources) >= INT_PAGE_SIZE:
                uid = shortuuid.encode(uuid.uuid4())
                storePage({"page": matched_resources[0:INT_PAGE_SIZE]}, uid)
                internal_page_id_list.append(uid)
                length_sum += INT_PAGE_SIZE
                matched_resources = matched_resources[INT_PAGE_SIZE:]

            link_index = [link["relation"] for link in response["link"]].index("next")
            corrected_url = (
                SERVER_URL + response["link"][link_index]["url"].split("/fhir/")[1]
            )

            response = s.get(corrected_url, auth=auth, verify=False).json()
            if LOG_LEVEL == "DEBUG":
                print(f"paged response: {response}")

            # Extract entries and relevant fields
            raw_resources = response["entry"]

            mapped_results = pool.map(
                partial(
                    matchResourcesWithConsents,
                    consents=all_consents,
                    resource_config=RESOURCE_PATHS[resource],
                    provision_config=prov_conf,
                ),
                raw_resources,
                chunksize=MP_CHUNK_SIZE,
            )
            for result in mapped_results:
                matched_resources.extend(result)

        # Trigger internal paging for remaining Elements
        uid = shortuuid.encode(uuid.uuid4())
        storePage({"page": matched_resources}, uid)
        internal_page_id_list.append(uid)
        length_sum += len(matched_resources)

        # Page results and return first page
        num_of_pages = math.ceil(length_sum / PAGE_SIZE)
        next_page_id = ""
        matched_resources = getPage(internal_page_id_list.pop(), True)["page"]
        for i in range(num_of_pages):
            if i + 1 == num_of_pages:
                topIndex = None
                botIndex = i * PAGE_SIZE
            else:
                topIndex = (i + 1) * PAGE_SIZE
                botIndex = i * PAGE_SIZE

            if topIndex != None and topIndex >= len(matched_resources):
                matched_resources.extend(
                    getPage(internal_page_id_list.pop(), True)["page"]
                )

            curr_page, next_page_id = fhirBundlifyList(
                list=matched_resources[botIndex:topIndex],
                total=len(matched_resources),
                uid=next_page_id,
                page_size=PAGE_SIZE,
                page_store_time=PAGE_STORE_TIME,
                facade_url=f"{request.url_root}fhir/",
                lastPage=(i + 1 == num_of_pages),
            )
            page_id_list.append(curr_page["id"])

            storePage(curr_page, curr_page["id"], PAGE_STORE_TIME)

        clearPages(PAGE_STORE_TIME)

        if len(page_id_list) != 0:
            return getPage(page_id_list[0])
        else:
            emptySearchPage, nextUid = fhirBundlifyList(
                list=[],
                total=0,
                page_size=PAGE_SIZE,
                page_store_time=PAGE_STORE_TIME,
                facade_url=f"{request.url_root}fhir/",
                lastPage=True,
            )
            storePage(emptySearchPage, emptySearchPage["id"], PAGE_STORE_TIME)
            return emptySearchPage


class FHIR_Facade_Server(Resource):
    def get(self, resource):
        return handleRequest(self, resource, "_search")

    def post(self, resource, search="False"):
        return handleRequest(self, resource, search)
