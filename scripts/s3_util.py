import os

import boto3

from config import BUCKET

s3 = boto3.client("s3")


def upload_path(local_path: str, s3_key: str, label: str) -> None:
    try:
        s3.upload_file(local_path, BUCKET, s3_key)
        print(f"[{label}] Uploaded: s3://{BUCKET}/{s3_key}")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)


def upload_bytes(body: bytes, s3_key: str, label: str) -> None:
    s3.put_object(Bucket=BUCKET, Key=s3_key, Body=body)
    print(f"[{label}] Uploaded: s3://{BUCKET}/{s3_key}")
