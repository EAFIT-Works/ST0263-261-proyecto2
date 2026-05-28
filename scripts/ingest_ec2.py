import datetime
import os

from config import BUCKET, LOCAL_DATA_PATH
from s3_util import s3


def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def upload_existing_csv(source_path: str, name: str) -> None:
    timestamp = ts()
    s3_key = f"raw/{name}/{name}_{timestamp}.csv"
    # Sube el CSV tal cual: sin pandas ni copia en /tmp.
    s3.upload_file(source_path, BUCKET, s3_key)
    print(f"[EC2 INGEST] Uploaded: s3://{BUCKET}/{s3_key}")


def ingest_ec2_files():
    files = {
        "movies": "movies.csv",
        "tv_shows": "tv_shows.csv",
    }

    for name, file in files.items():
        path = os.path.join(LOCAL_DATA_PATH, file)
        if os.path.exists(path):
            upload_existing_csv(path, name)
        else:
            print(f"[WARN] Missing file: {path}")
