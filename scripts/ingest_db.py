import pandas as pd
from sqlalchemy import create_engine
import boto3
import datetime

# =========================
# CONFIG
# =========================

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


# =========================
# UTIL
# =========================

def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def upload_to_s3(df, name):
    """Upload dataframe snapshot to S3 raw zone"""
    timestamp = ts()

    local_file = f"/tmp/{name}_{timestamp}.csv"
    s3_key = f"raw/{name}/{name}_{timestamp}.csv"

    df.to_csv(local_file, index=False)
    s3.upload_file(local_file, BUCKET, s3_key)

    print(f"[MARIADB INGEST] Uploaded: s3://{BUCKET}/{s3_key}")


def ingest_table(query, name):
    """Extract from MariaDB and load into S3"""
    df = pd.read_sql(query, engine)
    upload_to_s3(df, name)


# =========================
# PIPELINE RUN
# =========================

print("=== MARIADB INGEST START ===")

ingest_table("SELECT * FROM people", "people")
ingest_table("SELECT * FROM movie_reviews", "movie_reviews")

print("=== MARIADB INGEST END ===")
