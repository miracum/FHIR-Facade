# FHIR-Facade

## Deployment

### Environment Variables

| Variable                      | Default                       | Function                      | Comment                       |
|-------------------------------|:-----------------------------:|:-----------------------------:|:-----------------------------:|
| FACADE_PORT | 8082 | Port on which the Fhir-Facade is available | |
| FHIR_SERVER_URL               | http://localhost:8080/fhir/   | | |

### Standalone Deployment

In order to run the standalone facade simply run: 

`docker compose up`

### Test Deployment

Or run a facade test instance with a [blaze fhir server](https://github.com/samply/blaze) with:

`docker compose -f compose-with-blaze.yml up`


Use the uploadTestData.sh script to upload testdata to blaze

`./uploadTestData.sh`

All Data was randomly generated with [SyntheaTM](https://github.com/synthetichealth/synthea) and manually modified to include Consent (and its dependent) Resources based on the [MII Kerndatensatz](https://simplifier.net/packages/de.medizininformatikinitiative.kerndatensatz.consent/1.0.0-ballot1).

Both variants expose the facade-endpoint on :8082/fhir/ unless configured otherwise
