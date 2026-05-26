import boto3
import pandas as pd
import os
import datetime

BUCKET = "movie-analytics-lake"
LOCAL_PATH = "/home/ubuntu/project/data"

s3 = boto3.client("s3")


def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def upload(df, name):
    timestamp = ts()

    local_file = f"/tmp/{name}_{timestamp}.csv"
    s3_key = f"raw/{name}/{name}_{timestamp}.csv"

    df.to_csv(local_file, index=False)
    s3.upload_file(local_file, BUCKET, s3_key)

    print(f"[EC2 INGEST] Uploaded: {s3_key}")


def ingest_ec2_files():
    files = {
        "movies": "movies.csv",
        "tv_shows": "tv_shows.csv"
    }

    for name, file in files.items():
        path = os.path.join(LOCAL_PATH, file)

        if os.path.exists(path):
            df = pd.read_csv(path)
            upload(df, name)
        else:
            print(f"[WARN] Missing file: {path}")


print("=== EC2 INGEST START ===")
ingest_ec2_files()
print("=== EC2 INGEST END ===")
