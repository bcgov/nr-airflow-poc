# Airflow Proof of Concept Environment
This repository holds all the code related to the Airflow Proof of Concept environment with a sample data pipeline and a log cleaner. It has all the structures and auxiliary functionalities to move data between two databases, working only with Oracle and Postgres.

It runs on Docker containers using the docker-compose plugin to orchestrate three containers, all used for Airflow: 
- Scheduler.
- Webserver.
- Metadata database - in this case, a Postgres database.

The metadata database is running on a persistent volume so we won't lose data in case of stopping our container.

# Running the application
Once you have cloned this repository, to start the Airflow environment we first set an environment variable to tell the application which environment we are working on (dev, test, or prod). That value will be used on the DAGs to get the correct source and target database connections according to the environment - if we are running Airflow on test env then we should move data between test databases and if we are on prod env we should use prod databases. There is also a variable for the default configuration folder that should not be changed:

```
ENV AIRFLOW_ENV=dev
ENV AIRFLOW_CONFIG_PAHT=/opt/airflow
```

There is also a folder mapping under the volume area of docker-compose file:
```
volumes:
  - ./config:/opt/airflow/config
  - ./dags:/opt/airflow/dags
  - ./database_metadata:/opt/airflow/database_metadata
  - ./logs:/opt/airflow/logs
  - ./plugins:/opt/airflow/plugins
```

We then need to build the image from the Dockerfile by running the airflow-init section from the docker-compose.yml file:
```
docker-compose up airflow-init
```

And when the build ends we can start our applications:
```
docker-compose up
```
To use Airflow web interface just go to http://localhost:8080/ on your browser and use "airflow" as username and password. You should see two paused dags without any previous executions.

# Inside Airflow container
Once our environment is up and running we can get inside our containers if we need to run any Airflow commands. To log in to the container just type the following command replacing the "airflow_airflow-scheduler_1" for your container name:
```
docker exec -it airflow_airflow-scheduler_1 bash
```

When inside Airflow container we can run some commands to interact with the DAGs. We could restart our metadata database in order to capture changes in our DAGs:
```
airflow db init
```

We could list the DAGs:
```
airflow dags list
```

And we cloud even delete a DAG and all its metadata:
```
airflow dags delete YOUR_DAG_NAME
```

# Some considerations
- Besides the DAG file, there is a whole structure in order to move data from one database to another. All auxiliary modules/functionalities are under the modules folder inside the dags folder;
- There are three places you need to define the database configurations and they all should have a pattern:
  - First, in the database_config.json file, you set all the connections and name them with an environment suffix. For instance, if you have a spar_oracle database you should have a spar_oracle_dev, spar_oracle_tst, and spar_oracle_prd defined on this file.
  - Then under both source and target folders within the database_metadata folder, you should have a folder for each database you are using and it should be named without the suffix. If you defined spar_oracle_dev, spar_oracle_tst, and spar_oracle_prd on the database configuration file, you should have one folder named spar_oracle under the source folder and one under the target folder.
  - Finally, inside the DAG you need to define which is the source and target database you will be working on. For that use the exact name you have defined in the metadata_database folder - in our example, spar_oracle. Airflow will handle which environment it should use based on the environment variable defined on the Dockerfile.
- The way it is built, in order for data to be moved, you need to define an extraction file with the select statement and place it under the right folder (metadata_database/source/YOUR_DATABASE_FOLDER). That file must end with the column used as an incremental date extraction. For table SEEDLOT we are using the columns UPDATE_TIMESTAMP and the end of the file must look like this:
```
WHERE UPDATE_TIMESTAMP
```
- You also need a JSON file to describe your target table's metadata that should be placed under database_metadata/target/YOUR_DATABASE_NAME.
- You should not worry about incremental extraction dates, it is controlled by Airflow variables. Every new extraction will use a default value of 01/01/2023. Variables are named after the DAG id plus the task id and they are created only after the first task execution. If you need to change the extraction date you can change the variable on the web interface area under Admin - Variables.
- In order to move data, the structure build will extract data to a Python Pandas data frame, load them into a temporary table on the target database (working as a landing zone), merge data between the final target table and temporary table (it will perform an update statement and an insert statement) and will drop the temporary table.
