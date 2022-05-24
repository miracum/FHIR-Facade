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

## Provision Configuration
Provisions can be configured either before container startup in the general_provison_config.json or during runtime:
Pass a dictionary of provision codes based on the [MII Kerndatensatz](https://simplifier.net/packages/de.medizininformatikinitiative.kerndatensatz.consent/1.0.0-ballot1).

<code>
{
    "code":  [
        {
            "coding":  [
                {
                    "system": "urn:oid:2.16.840.1.113883.3.1937.777.24.5.3",
                    "code": "2.16.840.1.113883.3.1937.777.24.5.3.8",
                    "display": "MDAT_wissenschaftlich_nutzen_EU_DSGVO_NIVEAU"
                }
            ]
        }
    ]
    "code":  [
        {
            "coding":  [
                {
                    "system": "urn:oid:2.16.840.1.113883.3.1937.777.24.5.3",
                    "code": "2.16.840.1.113883.3.1937.777.24.5.3.5",
                    "display": "MDAT_Erheben"
                }
            ]
        }
    ]
}
</code>
