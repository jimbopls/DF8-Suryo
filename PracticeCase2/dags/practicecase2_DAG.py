import os
import logging

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from urllib.request import Request, urlopen

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator
import pyarrow.csv as pv
import pyarrow.parquet as pq
import pandas as pd
import json
import csv

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")


# dataset_file = "yellow_tripdata_2021-01.csv"
# dataset_url = f"https://s3.amazonaws.com/nyc-tlc/trip+data/{dataset_file}"

# dataset_file = "taxi+_zone_lookup.csv"
# dataset_url = f"https://d37ci6vzurychx.cloudfront.net/misc/{dataset_file}"

dataset_file = 'data.json'
dataset_file_csv = 'csvdata.csv'
dataset_url = f"https://datausa.io/api/data?drilldowns=Nation&measures=Population"

path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
parquet_file = dataset_file_csv.replace('.csv', '.parquet')
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'practice_case_2')

# access api and get dataset
def call_dataset(dataset_url):
    req = Request(
        url = dataset_url,
        headers = {'User-Agent': 'Mozilla/5.0'} # required or else will get 403 forbidden error
    )
    response = urlopen(req)
    data_json = json.loads(response.read())
    with open('data.json', 'w', encoding='utf-8') as f: # save file as .json
        json.dump(data_json['data'], f, indent=4)

# save as csv
def save_as_csv(dataset_file):
    df = pd.read_json(dataset_file)
    df['Year'] = df['Year'].apply(json.dumps) # required to preserve double quotes on 'Year' field for some reason
    print(df)
    df.to_csv(r'csvdata.csv', index=None, quoting=csv.QUOTE_NONNUMERIC)

def format_to_parquet(src_file):
    if not src_file.endswith('.csv'):
        logging.error("Can only accept source files in CSV format, for the moment")
        return
    table = pv.read_csv(src_file)
    pq.write_table(table, src_file.replace('.csv', '.parquet'))


# NOTE: takes 20 mins, at an upload speed of 800kbps. Faster if your internet has a better upload speed
def upload_to_gcs(bucket, object_name, local_file):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)


default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 0,
}

# NOTE: DAG declaration - using a Context Manager (an implicit way)
with DAG(
    dag_id="practice_case_2_dag",
    schedule_interval="@daily",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=['dtc-de'],
) as dag:

    call_dataset_task = PythonOperator(
        task_id="call_dataset_task",
        python_callable=call_dataset,
        op_kwargs={
            "dataset_url":dataset_url,
        },
    )

    save_as_csv_task = PythonOperator(
        task_id="save_as_csv_task",
        python_callable=save_as_csv,
        op_kwargs={
            "dataset_file":dataset_file,
        },
    )

    format_to_parquet_task = PythonOperator(
        task_id="format_to_parquet_task",
        python_callable=format_to_parquet,
        op_kwargs={
            "src_file": f"{path_to_local_home}/{dataset_file_csv}",
        },
    )

    local_to_gcs_task = PythonOperator(
        task_id="local_to_gcs_task",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/{parquet_file}",
            "local_file": f"{path_to_local_home}/{parquet_file}",
        },
    )

    bigquery_external_table_task = BigQueryCreateExternalTableOperator(
        task_id="bigquery_external_table_task",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": "external_table",
            },
            "externalDataConfiguration": {
                "sourceFormat": "PARQUET",
                "sourceUris": [f"gs://{BUCKET}/raw/{parquet_file}"],
            },
        },
    )

    call_dataset_task >> save_as_csv_task >> format_to_parquet_task >> local_to_gcs_task >> bigquery_external_table_task
