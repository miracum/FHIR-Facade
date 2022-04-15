# FHIR-Facade

## Deployment
In order to run the standalone facade simply run: 
`docker compose up`

Run a facade test instance with an included [blaze fhir server](https://github.com/samply/blaze) with:
`docker compose -f compose-with-blaze.yml up`

Both expose the facade-endpoint on :8082/fhir/ unless configured otherwise