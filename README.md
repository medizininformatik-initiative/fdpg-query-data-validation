# ABIDE Validation
This project provides a validation service in order to validate FHIR data
with respects to data quality, the requirements of the FDPG network and to 
ascertain what codes and values are most commonly used at the different sites.
Accordingly, the goal is not merely to assess data quality but also to 
facilitate mediation regarding how data has to be structured and has to be 
recorded for it to conform to the requirements of the FDPG platform.

## Deployment
This section will explore the deployment in an exemplary environment to not only provide information on
how to run this tool itself, but also on how to integrate it into existing software infrastructure.

1. **Provide FHIR server with data that you want to validate.** If you don't have a FHIR server already set up you view
     the **Deploying a FHIR server** section on how to start up the Blaze FHIR server and how to upload data on it.
2. **Pull this repository from GitHub using the command prompt and run**

```git clone https://github.com/medizininformatik-initiative/fdpg-query-data-validation.git```.

3. **Move into the project directory.** You can do this bei either opening the folder and starting a new command prompt
   from there or by running ```cd fdpg-query-data-validation``` in the command prompt you used in the previous step.
4. **Adjust the environment variables such that they fit the environment you want to run the validation tool in.** If
   the default ports used for the components of this are not blocked by other services, you will likely only have to 
   adjust the **FHIR_SERVER_URL** variable and (depending on your security setup) have to set values for the variables
   needed for your method of authentication. Refer to the **Configuration section for more details**.
5. **Download required value sets and code systems from [Confluence](https://confluence.imi.med.fau.de/pages/viewpage.action?pageId=218743453) and drop the extracted files into the value_sets
   directory.** They are necessary for the validation and have to be provided.
6. **For starting up the validation process you can now run**
   ```sh startup_and_run.sh``` 
   **in your command prompt.** If you want to restart the process after running it once already you can just run 
   ```sh run.sh```
   which will only restart the extraction script and not all other services. Conversely, if you want to shutdown the
   services used during validation you can simply run
   ```sh shutdown.sh```
   which will take care of the remaining services.

### Deploying a FHIR server
Before deploying this tool you need some FHIR server to which request can be made. This example will use
the [Blaze FHIR server](https://github.com/samply/blaze) which you can easily deploy using Docker with
the following commands:

```docker network create feasibility-deploy_default```

```docker volume create blaze-data```

```docker run -d --net=feasibility-deploy_default -p 8080:8080 -v blaze-data samply/blaze:0.18```

**NOTE:** Further documentation can be found [here](https://github.com/samply/blaze/blob/master/docs/deployment/docker-deployment.md)
**NOTE:** If you adjust the network name via the environment variable **PROJECT_CONTEXT** the network name would change
to *<project_context>_default* which you have to account for in the *docker network create* and *docker run* command

### Uploading data to Blaze FHIR server
Once the server is up and running you can upload your FHIR data to the server using the [FHIR REST API](https://www.hl7.org/fhir/http.html)
as implemented by every FHIR server. In the case of Blaze you can use the [blazectl tool](https://github.com/samply/blazectl).
It allows for easy data upload using the following command:

```blazectl upload <data_dir> --server <server_url>```

where **data_dir** is the directory your FHIR data in form of bundles (supported file formats can be found [here](https://github.com/samply/blazectl#upload))
and **server_url** is the URL of your FHIR server (in the case of this example it would be *http://localhost:8080/fhir*).

To obtain test data you can use the [KDS test data repository](https://github.com/medizininformatik-initiative/kerndatensatz-testdaten)
which you can grab by running 

```git clone https://github.com/medizininformatik-initiative/kerndatensatz-testdaten.git```

The repository contains the **Test_Data** folder which contains the FHIR bundles. To upload the contained data in this
example you would thus run

```blazectl upload kerndatensatz-testdaten/Test_Data --server http://localhost:8080/fhir```

to upload the data.

## Configuration
The environment variables can be configured in the **.env** file.

|             Key              |                                                                                                          Value                                                                                                           |
|:----------------------------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|       **SERVICE_PORT**       |                                                                               Port on which the service can be accessed as described above                                                                               |
|        **BLAZE_PORT**        |                                                                              Port on which the Blaze FHIR server can be accessed externally                                                                              |
|      **VALIDATOR_PORT**      |                                                                           Port on which the FHIR Marshal validator can be accessed externally                                                                            |
| **TERMINOLOGY_SERVICE_PORT** |                                                                                  Port of the terminology service used during validation                                                                                  |
|         **PACKAGES**         | String containing packages to load into the Blaze FHIR server and provide the necessary StructureDefinition instances for validation from [Simplifier](https://simplifier.net/). By default the KDS profiles are loaded  |
|     **FHIR_SERVER_URL**      |                                                                      URL of the FHIR server from which the data that will be validated is obtained                                                                       |
|     **PROJECT_CONTEXT**      |                                                                   The context in which both this tool and your FHIR server (data source) have to run.                                                                    |
|          **TOTAL**           |                                    Total number of instances for each relevant resource type (and unique LOINC code for Observation instances) which are pulled from the FHIR server                                     |
|          **COUNT**           |                                                                   Number of instances of a single page while paging through request to the FHIR server                                                                   |
|     **REPORT_LOCATION**      |                                                               Location on the machine where you can find the generated reports after successful execution                                                                |
|      **FHIR_USERNAME**       |                                                                               User name for authentication via BasicAuth and OAuth if used                                                                               |
|      **FHIR_PASSWORD**       |                                                                               Password for authentication via BasicAuth and OAuth if used                                                                                |
|        **FHIR_TOKEN**        |                                                                                               Token used for OAuth if used                                                                                               |
|        **HTTP_PROXY**        |                                                                                             URL of HTTP proxy server if used                                                                                             |
|       **HTTPS_PROXY**        |                                                                                            URL of HTTPS proxy server if used                                                                                             |
|       **CA_FILE_NAME**       |                                            File name of certificate file you can place into the **certificates** directory and want to use for authentication if you require                                             |
|  **FHIR_PROFILE_DIRECTORY**  |      Location of all the additional FHIR StructureDefinition instances you might want to use to validate again. Alternatively you can just drop them into the default location instead of providing a path to them       |
|   **VALUE_SET_DIRECTORY**    | Location of the **expanded** ValueSet instances you might require if you want to validate against your own profiles. Alternatively you can just drop them into the default location instead of providing a path to them. |

## Architecture
This validation tool consists out of multiple components each of which is serving a unique purpose. Upon startup, the 
**Extraction Script** requests relevant resource instances from your FHIR Server and validates the data the obtained 
bundles using the tools hidden behind the Validation API-Endpoint.

Bundles of FHIR data send to the **Validation API-Endpoint** where individual resource instances are matched with
special FHIR profiles (if provided) if they match the associated conditions as provided by the 
**validation_mapping.json** file in the **maps** directory. After modification, they are sent to
the [FHIR Marshal](https://github.com/itcr-uni-luebeck/fhir-marshal) which serves as the validator. 

For facilitating this task, it draws required StructureDefinition instances from a 
[Blaze FHIR server](https://github.com/samply/blaze). The [KDS profiles of the MII](https://simplifier.net/organization/koordinationsstellemii/~projects)
and their respective dependencies serve as a baseline and are provided using the [FHIR populator](https://pypi.org/project/fhir-populator/)
tool. Additional StructureDefinitions to possibly validate against can be uploaded by placing the respective
files in the **api/profiles** directory.

Additionally, a lightweight [terminology server](https://github.com/paulolaup/termite) is included to enable the 
validation against value sets and code systems. Value sets can be added by placing files containing
the **expanded(!)** version into the **api/terminology_data** folder.

The OperationOutcome instances generated during validation are returned to the Validation API-Endpoint layer and
returned to the extraction script.

The Extraction Script then matches the obtained OperationOutcome instances to respective instances in the original
bundles which where acquired during the initial requests to your FHIR server. Thus, the generated report allows users to
check their data for issues after validation is done. The reports can be found under the path specified in the 
**REPORT_LOCATION** environment variable (see *Configuration* section).

**NOTE:** No data not initially present during the build and startup phase of this tool is retained in the system and
neither is data obtained from your server

![alt text](architecture.PNG)
