import csv
import datetime
import gc
import io
from typing import Iterator

import pymysql

from config import (
    DB_FETCH_SIZE,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)
from s3_util import upload_stream


def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _connect():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.SSCursor,
        read_timeout=600,
        write_timeout=600,
    )


def _csv_byte_chunks(cursor, fetch_size: int) -> Iterator[bytes]:
    buf = io.StringIO()
    writer = csv.writer(buf)

    columns = [col[0] for col in cursor.description]
    writer.writerow(columns)
    yield buf.getvalue().encode("utf-8")
    buf.seek(0)
    buf.truncate(0)

    batches = 0
    while True:
        rows = cursor.fetchmany(fetch_size)
        if not rows:
            break
        writer.writerows(rows)
        yield buf.getvalue().encode("utf-8")
        buf.seek(0)
        buf.truncate(0)
        batches += 1
        if batches % 20 == 0:
            gc.collect()


def ingest_table(query: str, name: str, fetch_size: int = DB_FETCH_SIZE) -> None:
    timestamp = ts()
    s3_key = f"raw/{name}/{name}_{timestamp}.csv"

    conn = _connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            chunks = _csv_byte_chunks(cursor, fetch_size)
            first = next(chunks, None)
            if first is None:
                print(f"[WARN] No rows for table: {name}")
                return

            def all_chunks():
                yield first
                yield from chunks

            upload_stream(all_chunks(), s3_key, "DB INGEST")
            print(f"[DB INGEST] {name}: streaming OK (fetch_size={fetch_size})")
    finally:
        conn.close()
        gc.collect()
