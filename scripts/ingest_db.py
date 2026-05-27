import pandas as pd
from sqlalchemy import create_engine
import boto3
import datetime

BUCKET = "movie-analytics-lake"

DB_USER = "admin"
DB_PASSWORD = "admin123"
DB_HOST = "54.146.173.72"
DB_PORT = 3306
DB_NAME = "movies"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

s3 = boto3.client("s3")


def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def upload_to_s3(df, name):
    timestamp = ts()

    local_file = f"/tmp/{name}_{timestamp}.csv"
    s3_key = f"raw/{name}/{name}_{timestamp}.csv"

    df.to_csv(local_file, index=False)
    s3.upload_file(local_file, BUCKET, s3_key)

    print(f"[DB INGEST] Uploaded: s3://{BUCKET}/{s3_key}")


def ingest_table(query, name):
    df = pd.read_sql(query, engine)
    upload_to_s3(df, name)
