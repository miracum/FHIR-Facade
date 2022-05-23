import yaml, json, requests, os, math
from flask import Flask, request
from flask_restful import Resource
from util.consentAndResourceUtil import getAllConsents, matchResourcesWithConsents
from util.bundleUtil import fhirBundlifyList
from util.pagingStoreController import storePage, getPage, clearPages



#import config from yml files
global resource_config
with open('../config/resource_config.yml') as cfgfile:
    resource_config = yaml.safe_load(cfgfile)

RESOURCE_PATHS = resource_config['Resources']

class FHIR_Facade_Server(Resource):

    def get(self, resource):
        params = request.args.copy()
        SERVER_URL = os.environ['FHIR_SERVER_URL']
        try:
            prov_conf = json.loads(params["provision_config"])
        except:
            with open('../config/general_provision_config.json') as cfgfile:
                prov_conf = json.loads(cfgfile.read())
            print("no provision config, defaulting to config/general_provision_config.json")

        if(resource == "Page" and "__page-id" in params):
            return getPage(params["__page-id"])

        if(resource in RESOURCE_PATHS):
            #Check if resource has been configured properly
            if(RESOURCE_PATHS[resource]["Date"]=="" or RESOURCE_PATHS[resource]["Subject"]==""):
                return f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.", 403

            #refreshAllConsents
            all_consents = getAllConsents(SERVER_URL)
            page_size = int(os.environ["PAGE_SIZE"])
            page_store_time = int(os.environ["PAGE_STORE_TIME"])
            raw_resources = []
            matched_resources = []
            page_id_list = []

            #get initial resources from fhir server
            s = requests.session()
            
            response = s.get(SERVER_URL + resource, params=params, headers=request.headers, verify=False).json()
            if("entry" in response.keys()):
                raw_resources = response["entry"]
                matched_resources = matchResourcesWithConsents(resources=raw_resources,consents=all_consents,resource_config=RESOURCE_PATHS[resource], provision_config=prov_conf)

            #Iterate over potential paged responses
            while("next" in [link["relation"] for link in response["link"]]):

                link_index = [link["relation"] for link in response["link"]].index("next")
                corrected_url = SERVER_URL + response["link"][link_index]["url"].split("/fhir/")[1]

                response = s.get(corrected_url, verify=False).json()

                #Extract entries and relevant fields
                raw_resources = response["entry"]
            
                matched_resources = matched_resources + matchResourcesWithConsents(resources=raw_resources,consents=all_consents,resource_config=RESOURCE_PATHS[resource], provision_config=prov_conf)

            #Page results and return first page
            num_of_pages = math.ceil(len(matched_resources)/page_size)
            next_page_id = ""
            for i in range(num_of_pages):
                if(i+1 == num_of_pages):
                    topIndex = -1
                    botIndex = i*page_size
                else:
                    topIndex = (i+1)*page_size
                    botIndex = i*page_size

                curr_page, next_page_id = fhirBundlifyList(list=matched_resources[botIndex:topIndex],
                                            total=len(matched_resources),
                                            uid=next_page_id,
                                            page_size=page_size,
                                            page_store_time=page_store_time,
                                            facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                                            lastPage=(i+1 == num_of_pages))
                page_id_list.append(curr_page["id"])
                
                storePage(curr_page, curr_page["id"]) 

            print(len(matched_resources))
            print(matched_resources)

            clearPages(page_store_time)

            if(len(page_id_list)!=0):
                return getPage(page_id_list[0])
            else:
                emptySearchPage, nextUid = fhirBundlifyList(list=[],
                                    total=0,
                                    page_size=page_size,
                                    page_store_time=page_store_time,
                                    facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                                    lastPage=True)
                storePage(emptySearchPage, emptySearchPage["id"])
                return emptySearchPage

        else:
            return f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.", 403



    def post(self, resource, search='false'):
        SERVER_URL = os.environ['FHIR_SERVER_URL']

        if(search == '_search'):
            params = request.args.copy()

            if(resource == "Page" and "__page-id" in params):
                return getPage(params["__page-id"])

            if(resource in RESOURCE_PATHS):
                #Check if resource has been configured properly
                if(RESOURCE_PATHS[resource]["Date"]=="" or RESOURCE_PATHS[resource]["Subject"]==""):
                    return f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.", 403

                #refreshAllConsents
                all_consents = getAllConsents(SERVER_URL)
                page_size = int(os.environ["PAGE_SIZE"])
                page_store_time = int(os.environ["PAGE_STORE_TIME"])
                matched_resources = []
                raw_resources = []
                page_id_list = []

                #get initial resources from fhir server
                s = requests.session()
                try:
                    data = json.loads(request.data)
                    data.update(params)
                except:
                    data = {}
                    data.update(params)

                try:
                    prov_conf = json.loads(data["provision_config"])
                except:
                    with open('../config/general_provision_config.json') as cfgfile:
                        prov_conf = json.loads(cfgfile.read())
                    print("no provision config, defaulting to config/general_provision_config.json")

                response = s.post(SERVER_URL + resource + '/_search', params=data, verify=False).json()
                if("entry" in response.keys()):
                    raw_resources = response["entry"]
                    matched_resources = matchResourcesWithConsents(resources=raw_resources,consents=all_consents,resource_config=RESOURCE_PATHS[resource], provision_config=prov_conf)

                #Iterate over potential paged responses
                while("next" in [link["relation"] for link in response["link"]]):

                    link_index = [link["relation"] for link in response["link"]].index("next")
                    corrected_url = SERVER_URL + response["link"][link_index]["url"].split("/fhir/")[1]

                    response = s.get(corrected_url, verify=False).json()

                    #Extract entries and relevant fields
                    raw_resources = response["entry"]
                
                    matched_resources = matched_resources + matchResourcesWithConsents(resources=raw_resources,consents=all_consents,resource_config=RESOURCE_PATHS[resource], provision_config=prov_conf)

                #Page results and return first page
                num_of_pages = math.ceil(len(matched_resources)/page_size)
                next_page_id = ""
                for i in range(num_of_pages):
                    if(i+1 == num_of_pages):
                        topIndex = -1
                        botIndex = i*page_size
                    else:
                        topIndex = (i+1)*page_size
                        botIndex = i*page_size

                    curr_page, next_page_id = fhirBundlifyList(list=matched_resources[botIndex:topIndex],
                                                total=len(matched_resources),
                                                uid=next_page_id,
                                                page_size=page_size,
                                                page_store_time=page_store_time,
                                                facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                                                lastPage=(i+1 == num_of_pages))
                    page_id_list.append(curr_page["id"])
                    
                    storePage(curr_page, curr_page["id"]) 

                clearPages(page_store_time)

                if(len(page_id_list)!=0):
                    return getPage(page_id_list[0])
                else:
                    emptySearchPage, nextUid = fhirBundlifyList(list=[],
                                        total=0,
                                        page_size=page_size,
                                        page_store_time=page_store_time,
                                        facade_url=f"https://localhost:{(os.environ['FACADE_PORT'])}/fhir/",
                                        lastPage=True)
                    storePage(emptySearchPage, emptySearchPage["id"])
                    return emptySearchPage

            else:
                return f"The requested resource has not been configured. Please add the necessary configuration. Or if you dont require consent for the requested resources, use the fhir-server endpoint ({SERVER_URL}) directly.", 403
        else:
            return 'Syntax error. Use the appropriate fhir-post-search syntax: .../fhir/type/_search'