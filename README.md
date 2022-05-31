# FHIR-Facade

## Deployment

### Environment Variables

| Variable                      | Default                       | Function                      | Comment                       |
|-------------------------------|:-----------------------------:|:-----------------------------:|:-----------------------------:|
| FACADE_PORT | 8082 | Port on which the Fhir-Facade is available | |
| FHIR_SERVER_URL               | http://host.docker.internal:8080/fhir/   | | |
| PAGE_SIZE | 50 | Number of entries per result page | |
| PAGE_STORE_TIME | 1200 | Seconds after which queried pages are discarded | |
| INTERNAL_PAGE_SIZE | 2000 | Number of loaded resources, before internal paging is used||
| PAGING_STORE | LOCAL | Use local storage or MongoDb for paging | Valid values: LOCAL / MONGO |
| MONGO_DB_URL | mongodb://host.docker.internal:27017 | MongoDB Connection String | |
| LOG_LEVEL | INFO | Determines the amount of console output | Valid values: INFO / DEBUG |
| BA_USER_NAME | | BasicAuth username if required for the connection to the fhir server | |
| BA_PASSWORD | | BasicAuth password if required for the connection to the fhir server | |


### Standalone Deployment

In order to run the standalone facade from the cloned repository simply run: 

`docker compose up`

Or pull the build image from [dockerhub](https://hub.docker.com/repository/docker/boehmdo/fhir-facade)

### Test Deployment

Or run a facade test instance with a [blaze fhir server](https://github.com/samply/blaze) with:

`docker compose -f compose-with-blaze.yml up`


Use the uploadTestData.sh script to upload testdata to blaze

`./uploadTestData.sh`

All Data was randomly generated with [SyntheaTM](https://github.com/synthetichealth/synthea) and manually modified to include Consent (and its dependent) Resources based on the [MII Kerndatensatz](https://simplifier.net/packages/de.medizininformatikinitiative.kerndatensatz.consent/1.0.0-ballot1).

Both variants expose the facade-endpoint on :8082/fhir/ unless configured otherwise

## Configuration

### Resource Configuration
All Resources that are supposed to be accessed via the facade have to be configured in the config/resource_config.yml file. It is required that for every resource there is a path from the base resource to a subject/patient and the relevant date with regards to consent.

```
Resources:
  Observation:
    Date: "issued"
    Subject: "subject/reference"
  Encounter:
    Date: "period/start"
    Subject: "subject/reference"
```

### Provision Configuration
Provisions can be configured either before container startup in the config/general_provison_config.json or during runtime:
Pass a List of provision codes in a json format based on the [MII Kerndatensatz](https://simplifier.net/packages/de.medizininformatikinitiative.kerndatensatz.consent/1.0.0-ballot1).
Every Consent is required to have ALL provided provisions as a subset of its provision. This structure is required for the preconfiguration as well as the parameter version.


<code>
{
    "coding":  [
        {
            "system": "urn:oid:2.16.840.1.113883.3.1937.777.24.5.3",
            "code": "2.16.840.1.113883.3.1937.777.24.5.3.8"
        }
    ]   
}
</code>
