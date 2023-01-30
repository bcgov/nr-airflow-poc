# -*- coding: utf-8 -*-
import os
from module import utils as utils
from module import database_utils as db_utils


from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.log.logging_mixin import LoggingMixin

from datetime import datetime, timedelta

# Defining source and target databases
src_db_name = 'spar_postgres'
tgt_db_name = 'spar_oracle'

# Defining tables metadata
src_seedlot_file_name = 'SEEDLOT.sql'
tgt_seedlot_file_name = 'SEEDLOT.json'

src_forest_client_file_name = 'FOREST_CLIENT.sql'
tgt_forest_client_file_name = 'FOREST_CLIENT.json'

src_seedlot_owner_quantity_file_name = 'SEEDLOT_OWNER_QUANTITY.sql'
tgt_seedlot_owner_quantity_file_name = 'SEEDLOT_OWNER_QUANTITY.json'

# Defining pipeline (DAG) tags
tags = ['seedlot', 'forest_client', 'seedlot_owner_quantity']

# Loading airflow parameters from env variables
airflow_config_path = os.environ.get('AIRFLOW_CONFIG_PAHT')
airflow_env = os.environ.get('AIRFLOW_ENV')

# Loading DAG and database parameters from configuration file
dag_config = utils.open_json_file('{}/config/dag_config.json'.format(airflow_config_path))
db_config = utils.open_json_file('{}/config/database_config.json'.format(airflow_config_path))

# Loading source and target database connections parameters
src_db_config = db_config['{}_{}'.format(src_db_name, airflow_env)]
tgt_db_config = db_config['{}_{}'.format(tgt_db_name, airflow_env)]

# Loading extraction queries and target tables metadata
src_metadata_path = '{}/database_metadata/source/{}/'.format(airflow_config_path, src_db_name)
tgt_metadata_path = '{}/database_metadata/target/{}/'.format(airflow_config_path, tgt_db_name)

# Loading pipeline (DAG) default arguments
dag_args = dag_config['default_args']
default_args = {
    'owner': dag_args['owner'],
    'depends_on_past': eval(dag_args['depends_on_past']),
    'retries': dag_args['retries'],
    'retry_delay': timedelta(seconds=dag_args['retry_delay_seconds']),
    'max_active_runs': dag_args['max_active_runs'],
    'max_active_tasks': dag_args['max_active_tasks'],
    'email_on_failure': eval(dag_args['email_on_failure']),
    'email': dag_args['email']
}

with DAG(
    'Sync_SeedlotManagement',
    start_date=datetime(2023, 1, 1),
    schedule_interval='0 1 * * *', 
    catchup=eval(dag_args['catchup']),
    default_args=default_args,
    tags=tags
) as dag:
        
    StartDAG = DummyOperator(
        task_id='dag_start'
        )

    SyncSeedlotTable = PythonOperator(
        task_id='sync_seedlot_table',
        provide_context=True,
        python_callable=db_utils.sync_data,   
        op_kwargs={
                'src_query': utils.get_query_from_file(
                    src_metadata_path, src_seedlot_file_name), 
                'tgt_table_metadata': utils.open_json_file('{}{}'.format(
                    tgt_metadata_path, tgt_seedlot_file_name)),                
                'src_db_config': src_db_config,                
                'tgt_db_config': tgt_db_config
                }
        ) 

    SyncForestClientTable = PythonOperator(
        task_id='sync_forest_client_table',
        provide_context=True,
        python_callable=db_utils.sync_data,   
        op_kwargs={
                'src_query': utils.get_query_from_file(
                    src_metadata_path, src_forest_client_file_name), 
                'tgt_table_metadata': utils.open_json_file('{}{}'.format(
                    tgt_metadata_path, tgt_forest_client_file_name)),                
                'src_db_config': src_db_config,                
                'tgt_db_config': tgt_db_config
                }
        ) 

    SyncSeedlotOwnerQuantityTable = PythonOperator(
        task_id='sync_seedlot_owner_quantity_table',
        provide_context=True,
        python_callable=db_utils.sync_data,   
        op_kwargs={
                'src_query': utils.get_query_from_file(
                    src_metadata_path, src_seedlot_owner_quantity_file_name), 
                'tgt_table_metadata': utils.open_json_file('{}{}'.format(
                    tgt_metadata_path, tgt_seedlot_owner_quantity_file_name)),                
                'src_db_config': src_db_config,                
                'tgt_db_config': tgt_db_config
                }
        ) 

    StartDAG >> [SyncSeedlotTable, SyncForestClientTable] >> SyncSeedlotOwnerQuantityTable
