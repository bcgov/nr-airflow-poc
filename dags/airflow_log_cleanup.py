import logging
import os
from module import utils as utils
from datetime import datetime, timedelta

import airflow
import jinja2
from airflow.configuration import conf
from airflow.models import DAG, Variable
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator

# Defining pipeline (DAG) tags
tags = ['log_cleanup']

# Loading airflow parameters from env variables
airflow_config_path = os.environ.get('AIRFLOW_CONFIG_PAHT')

# Loading JSON properties
dag_config = utils.open_json_file('{}/config/dag_config.json'.format(airflow_config_path))
dag_args = dag_config['default_args']

try:
    BASE_LOG_FOLDER = conf.get("core", "BASE_LOG_FOLDER").rstrip("/")
except Exception as e:
    BASE_LOG_FOLDER = conf.get("logging", "BASE_LOG_FOLDER").rstrip("/")

# Amount of days logs will be retained
DEFAULT_MAX_LOG_AGE_IN_DAYS = 1
ENABLE_DELETE = True
NUMBER_OF_WORKERS = 1
DIRECTORIES_TO_DELETE = [BASE_LOG_FOLDER]
ENABLE_DELETE_CHILD_LOG = "True"
LOG_CLEANUP_PROCESS_LOCK_FILE = "/tmp/airflow_log_cleanup_worker.lock"
logging.info("ENABLE_DELETE_CHILD_LOG  " + ENABLE_DELETE_CHILD_LOG)

if not BASE_LOG_FOLDER or BASE_LOG_FOLDER.strip() == "":
    raise ValueError(
        "BASE_LOG_FOLDER variable is empty in airflow.cfg. It can be found "
        "under the [core] (<2.0.0) section or [logging] (>=2.0.0) in the cfg file. "
        "Kindly provide an appropriate directory path."
    )

if ENABLE_DELETE_CHILD_LOG.lower() == "true":
    try:
        CHILD_PROCESS_LOG_DIRECTORY = conf.get(
            "scheduler", "CHILD_PROCESS_LOG_DIRECTORY"
        )
        if CHILD_PROCESS_LOG_DIRECTORY != ' ':
            DIRECTORIES_TO_DELETE.append(CHILD_PROCESS_LOG_DIRECTORY)
    except Exception as e:
        logging.exception(
            "Could not obtain CHILD_PROCESS_LOG_DIRECTORY from " +
            "Airflow Configurations: " + str(e)
        )

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

dag = DAG(
    'Airflow_Log_Cleanup',
    start_date=datetime(2023, 1, 1),
    schedule_interval='0 3 * * *', # timedelta(days=1),
    template_undefined=jinja2.Undefined,
    catchup=eval(dag_args['catchup']),
    default_args=default_args,
    tags=tags
)

if hasattr(dag, 'doc_md'):
    dag.doc_md = __doc__
if hasattr(dag, 'catchup'):
    dag.catchup = False

start = DummyOperator(
    task_id='start',
    dag=dag)

log_cleanup = """

echo "Getting Configurations..."
BASE_LOG_FOLDER="{{params.directory}}"
WORKER_SLEEP_TIME="{{params.sleep_time}}"

sleep ${WORKER_SLEEP_TIME}s

MAX_LOG_AGE_IN_DAYS="{{dag_run.conf.maxLogAgeInDays}}"
if [ "${MAX_LOG_AGE_IN_DAYS}" == "" ]; then
    echo "maxLogAgeInDays conf variable isn't included. Using Default '""" + str(DEFAULT_MAX_LOG_AGE_IN_DAYS) + """'."
    MAX_LOG_AGE_IN_DAYS='""" + str(DEFAULT_MAX_LOG_AGE_IN_DAYS) + """'
fi
ENABLE_DELETE=""" + str("true" if ENABLE_DELETE else "false") + """
echo "Finished Getting Configurations"
echo ""

echo "Configurations:"
echo "BASE_LOG_FOLDER:      '${BASE_LOG_FOLDER}'"
echo "MAX_LOG_AGE_IN_DAYS:  '${MAX_LOG_AGE_IN_DAYS}'"
echo "ENABLE_DELETE:        '${ENABLE_DELETE}'"

cleanup() {
    echo "Executing Find Statement: $1"
    FILES_MARKED_FOR_DELETE=`eval $1`
    echo "Process will be Deleting the following File(s)/Directory(s):"
    echo "${FILES_MARKED_FOR_DELETE}"
    echo "Process will be Deleting `echo "${FILES_MARKED_FOR_DELETE}" | \
    grep -v '^$' | wc -l` File(s)/Directory(s)"     \
    # "grep -v '^$'" - removes empty lines.
    # "wc -l" - Counts the number of lines
    echo ""
    if [ "${ENABLE_DELETE}" == "true" ];
    then
        if [ "${FILES_MARKED_FOR_DELETE}" != "" ];
        then
            echo "Executing Delete Statement: $2"
            eval $2
            DELETE_STMT_EXIT_CODE=$?
            if [ "${DELETE_STMT_EXIT_CODE}" != "0" ]; then
                echo "Delete process failed with exit code \
                    '${DELETE_STMT_EXIT_CODE}'"

                echo "Removing lock file..."
                rm -f """ + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """
                if [ "${REMOVE_LOCK_FILE_EXIT_CODE}" != "0" ]; then
                    echo "Error removing the lock file. \
                    Check file permissions.\
                    To re-run the DAG, ensure that the lock file has been \
                    deleted (""" + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """)."
                    exit ${REMOVE_LOCK_FILE_EXIT_CODE}
                fi
                exit ${DELETE_STMT_EXIT_CODE}
            fi
        else
            echo "WARN: No File(s)/Directory(s) to Delete"
        fi
    else
        echo "WARN: You're opted to skip deleting the File(s)/Directory(s)!!!"
    fi
}


if [ ! -f """ + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """ ]; then

    echo "Lock file not found on this node! \
    Creating it to prevent collisions..."
    touch """ + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """
    CREATE_LOCK_FILE_EXIT_CODE=$?
    if [ "${CREATE_LOCK_FILE_EXIT_CODE}" != "0" ]; then
        echo "Error creating the lock file. \
        Check if the airflow user can create files under tmp directory. \
        Exiting..."
        exit ${CREATE_LOCK_FILE_EXIT_CODE}
    fi

    echo ""
    echo "Running Cleanup Process..."

    FIND_STATEMENT="find ${BASE_LOG_FOLDER}/*/* -type f -mtime \
     +${MAX_LOG_AGE_IN_DAYS}"
    DELETE_STMT="${FIND_STATEMENT} -exec rm -f {} \;"

    cleanup "${FIND_STATEMENT}" "${DELETE_STMT}"
    CLEANUP_EXIT_CODE=$?

    FIND_STATEMENT="find ${BASE_LOG_FOLDER}/*/* -type d -empty"
    DELETE_STMT="${FIND_STATEMENT} -prune -exec rm -rf {} \;"

    cleanup "${FIND_STATEMENT}" "${DELETE_STMT}"
    CLEANUP_EXIT_CODE=$?

    FIND_STATEMENT="find ${BASE_LOG_FOLDER}/* -type d -empty"
    DELETE_STMT="${FIND_STATEMENT} -prune -exec rm -rf {} \;"

    cleanup "${FIND_STATEMENT}" "${DELETE_STMT}"
    CLEANUP_EXIT_CODE=$?

    echo "Finished Running Cleanup Process"

    echo "Deleting lock file..."
    rm -f """ + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """
    REMOVE_LOCK_FILE_EXIT_CODE=$?
    if [ "${REMOVE_LOCK_FILE_EXIT_CODE}" != "0" ]; then
        echo "Error removing the lock file. Check file permissions. To re-run the DAG, ensure that the lock file has been deleted (""" + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """)."
        exit ${REMOVE_LOCK_FILE_EXIT_CODE}
    fi

else
    echo "Another task is already deleting logs on this worker node. \
    Skipping it!"
    echo "If you believe you're receiving this message in error, kindly check \
    if """ + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """ exists and delete it."
    exit 0
fi

"""

for log_cleanup_id in range(1, NUMBER_OF_WORKERS + 1):

    for dir_id, directory in enumerate(DIRECTORIES_TO_DELETE):

        log_cleanup_op = BashOperator(
            task_id='log_cleanup_worker_num_' +
            str(log_cleanup_id) + '_dir_' + str(dir_id),
            bash_command=log_cleanup,
            params={
                "directory": str(directory),
                "sleep_time": int(log_cleanup_id)*3},
            dag=dag)

        log_cleanup_op.set_upstream(start)