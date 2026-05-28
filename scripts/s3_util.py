import io
import os
from typing import Iterator

import boto3

from config import BUCKET

s3 = boto3.client("s3")


class _StreamReader:
    """Adapta un iterador de bytes para boto3 upload_fileobj."""

    def __init__(self, chunks: Iterator[bytes]):
        self._chunks = chunks
        self._buf = b""
        self._done = False

    def read(self, amt: int = 1024 * 1024) -> bytes:
        while len(self._buf) < amt and not self._done:
            try:
                self._buf += next(self._chunks)
            except StopIteration:
                self._done = True
                break
        out = self._buf[:amt]
        self._buf = self._buf[amt:]
        return out


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


def upload_stream(chunks: Iterator[bytes], s3_key: str, label: str) -> None:
    """Sube a S3 sin archivo local (evita llenar /tmp)."""
    s3.upload_fileobj(_StreamReader(chunks), BUCKET, s3_key)
    print(f"[{label}] Uploaded: s3://{BUCKET}/{s3_key}")
