from dateutil import parser 
from unittest import result
import requests, os
from requests.auth import HTTPBasicAuth

LOG_LEVEL = os.environ["LOG_LEVEL"]

def getAllConsents(SERVER_URL):

    #Get request for all consents
    raw_consents = []

    #Initial request and processing
    s = requests.session()
    auth=HTTPBasicAuth(os.getenv("BA_USER_NAME",""),os.getenv("BA_PASSWORD",""))
    response = s.get(SERVER_URL + "Consent", auth=auth, verify=False).json()

    if(LOG_LEVEL=="DEBUG"): print(f"Initial consent response: {response}")
    
    if("entry" in response.keys()):
        raw_consents = [entry["resource"] for entry in response["entry"]]

    #Iterate over potential paged responses
    while("next" in [link["relation"] for link in response["link"]]):

        link_index = [link["relation"] for link in response["link"]].index("next")
        corrected_url = SERVER_URL + response["link"][link_index]["url"].split("/fhir/")[1]

        response = s.get(corrected_url, auth=auth, verify=False)

        #Extract entries and relevant fields
        raw_consents = raw_consents + [entry["resource"] for entry in response["entry"]]

    return filterConsents(raw_consents)

def filterConsents(consents):

    filtered_consents = []

    #filter Consents based on the configured provisions
    for consent in consents:
        fits_config = True

        #check consent for required conditions
        try:
            #check consent.status = active
            if(not consent["status"]=="active"):
                fits_config = False
            if(not consent["resourceType"]=="Consent"):
                fits_config = False
        except:
            fits_config = False

        if(fits_config):
            filtered_consents.append(consent)

    return filtered_consents

def getProvisionTimeSet(consents, provision_config):
    provision_time_set = {}
    conf_prov_codes = provision_config["coding"]

    for consent in consents:

        patient = consent["patient"]["reference"]

        for provision in consent["provision"]["provision"]:

            provision_coding = provision["code"][0]["coding"][0]
            
            #check whether configured provisions are a subset of the consent provisions
            if(True in [(all(provision_coding.get(key, None) == val for key, val in config_code.items())) for config_code in conf_prov_codes]):
                
                try:
                    temp = provision_time_set[patient]
                except:
                    temp = []
                updated_provisions = temp + [{"code": provision_coding["code"],"type":provision["type"], "period": provision["period"]}]
                
                provision_time_set[patient] = updated_provisions

    return provision_time_set

def matchResourcesWithConsents(resources, consents, resource_config, provision_config):
    
    if(LOG_LEVEL=="DEBUG"): print(f"resource_config: {resource_config}")
    if(LOG_LEVEL=="DEBUG"): print(f"provision_config: {provision_config}")

    provision_time_set = getProvisionTimeSet(consents, provision_config)
    if(LOG_LEVEL=="DEBUG"): print(f"provision_time_set:{provision_time_set}")

    consented_resources = []

    for res in resources:

        is_consented = False

        #Get patient and date references from the resource via the configured path
        subject = res["resource"] 
        for path in resource_config["Subject"].split("/"):
            subject = subject[path]

        date = res["resource"]
        for path in resource_config["Date"].split("/"):
            date = date[path]
        date = parser.parse(date)

        if(subject in provision_time_set):
            for provision in provision_time_set[subject]:

                start = parser.parse(provision["period"]["start"])
                end = parser.parse(provision["period"]["end"])

                if(provision["type"]=="permit"):
                    if(date.timestamp()>=start.timestamp() and date.timestamp()<=end.timestamp()):
                        is_consented = True
                else:
                    if(date.timestamp()>=start.timestamp() and date.timestamp()<=end.timestamp()):
                        is_consented = False
                        break

        if(is_consented):
            consented_resources.append(res)

    return consented_resources