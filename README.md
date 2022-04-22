# FHIR-Facade

## Deployment

First, intialize the default environment

`cp .default-env .env`

In order to run the standalone facade simply run: 

`docker compose up`

Or run a facade test instance with a [blaze fhir server](https://github.com/samply/blaze) with:

`docker compose -f compose-with-blaze.yml up`

Both variants expose the facade-endpoint on :8082/fhir/ unless configured otherwise
