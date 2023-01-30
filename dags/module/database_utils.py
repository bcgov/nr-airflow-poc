import pandas as pd
from module import utils
from module import database_connection as db_conn
from airflow.utils.log.logging_mixin import LoggingMixin
from airflow.operators.python import get_current_context
from airflow.models import Variable
from datetime import datetime

def extract_data(src_query: str,                    
                tgt_table_metadata: str,
                src_conn: object, 
                tgt_conn: object, 
                src_db_type: str,
                incremental_extraction_date: str,
                chunk_size: int, **kwargs) -> None:
        """
        Extracts data from the source database and loads it in a temporary table in the target database.
        First creates the temporary table in the target database, then executes the query and loads data 
        into the temp table. 
        The temporary table name is defined by the first 26 characters of the table_name property set in 
        the tgt_table_metadata with a 'TMP_' prefix added to it.
        If an exception occurs, tries to drop the previously created temp table.

        Parameters
        ----------
        src_query: str
            SQL statement used to extract data from the source database.
        tgt_table_metadata: str
            Target table metadata - usually stored in a JSON file and extracted into a string (dict).
        src_conn: object
            Source database connection object from where data will be extracted.
        tgt_conn: object
            Target database connection object to where temporary data will be loaded.
        src_db_type: str
            Source Database type - can be ORACLE os POSTGRES.
        incremental_extraction_date: str
            Only data that are created or update after the incremental extraction date will be synced.
        chunk_size: int
            Chunk size used by pandas dataframe to move data from source to target.         
        """
        try: 
            LoggingMixin().log.info('*** Data Sync *** Incremental extraction date: {}'.format(incremental_extraction_date[:16]))
            src_query = utils.add_incremental_date_to_query(src_query, incremental_extraction_date[:16], src_db_type)

            tgt_conn.execute(utils.metadata_to_create_table_qry(tgt_table_metadata))
            for df in pd.read_sql(src_query, src_conn.engine, chunksize=chunk_size):
                df.to_sql(utils.format_temp_table_name(tgt_table_metadata), tgt_conn.engine, 
                    index=False, if_exists="append", chunksize=chunk_size)
                LoggingMixin().log.info('*** Data Sync *** Target table name: {}'.format(tgt_table_metadata['table_name']))
                LoggingMixin().log.info('*** Data Sync *** Number of rows to be merged: {}'.format(df.shape[0]))
        except Exception as e:
            tgt_conn.execute(utils.metadata_to_drop_table_qry(tgt_table_metadata))
            raise Exception("Data extraction error. Message: {}".format(e))

def load_data(tgt_table_metadata: str,
            tgt_conn: object, 
            tgt_db_type: str, **kwargs) -> None:
        """
        Loads data from a temporary table into the final table defined in the table_metadata.
        Executes an insert and an update SQL statement - similar to a merge operation - based on the 
        table_name and columns properties defined in the table_metadata.
        After all data is loaded, drops the temporary table - the temp table will be dropped even in 
        the occurrence of an exception.

        Parameters
        ----------
        tgt_table_metadata: str
            Target table metadata usually stored in a JSON file and extracted into a string (dict).
        tgt_conn: object
            Database connection object where data will be loaded.
        tgt_db_type: str
            Database type. Can be ORACLE or POSTGRES.
        """
        try:
            if tgt_db_type == 'ORACLE':
                tgt_conn.execute(utils.metadata_to_oracle_update_qry(tgt_table_metadata))
            if tgt_db_type == 'POSTGRES':
                tgt_conn.execute(utils.metadata_to_postgres_update_qry(tgt_table_metadata))

            tgt_conn.execute(utils.metadata_to_insert_qry(tgt_table_metadata))
            
        except Exception as e:
            raise Exception("Data load error. Message: {}".format(e))
        finally:
            tgt_conn.execute(utils.metadata_to_drop_table_qry(tgt_table_metadata))

def sync_data(src_query: str,                    
            tgt_table_metadata: str,
            src_db_config: str, 
            tgt_db_config: str, 
            chunk_size=200, **kwargs) -> None:
        """
        Syncs data from two tables in different databases using a query to extract data and 
        tgt_table_metadata defined properties to load data by calling extract_data and load_data 
        functions.

        Parameters
        ----------
        src_query: str
            SQL statement used to extract data from the source database.
        tgt_table_metadata: str
            Target table metadata usually stored in a JSON file and extracted into a string (dict).
        src_db_config: str
            Source database connection configurations from where data will be extracted.
        tgt_db_config: str
            Target database connection configurations to where data will be loaded.
        chunk_size: int, default 200
            Chunk size used by pandas dataframe to move data from source to target.             
        """
        try: 

            # Sets auto incremental date
            DEFAULT_EXTRACTION_DATE = '2023-01-01 00:00'
            context = get_current_context()
            ti = context['ti']
            incremental_extraction_date = Variable.get(
                    key='{}.{}'.format(ti.dag_id, ti.task_id), 
                    deserialize_json=False, 
                    default_var=DEFAULT_EXTRACTION_DATE
                    )
            task_start_date = datetime.now()

            with db_conn.database_connection(tgt_db_config) as tgt_conn:
                with db_conn.database_connection(src_db_config) as src_conn:
                    extract_data(src_query, tgt_table_metadata, src_conn, tgt_conn, src_db_config['type'], incremental_extraction_date, chunk_size)
                load_data(tgt_table_metadata, tgt_conn, tgt_db_config['type'])

            Variable.set(key='{}.{}'.format(ti.dag_id, ti.task_id), value=task_start_date, serialize_json=False)
        except Exception as e:
            raise Exception("Data sync error. Message: {}".format(e))