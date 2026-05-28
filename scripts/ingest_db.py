import csv
import datetime
import gc
import os

import pymysql

from config import (
    DB_FETCH_SIZE,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)
from s3_util import upload_path


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


def ingest_table(query: str, name: str, fetch_size: int = DB_FETCH_SIZE) -> None:
    """
    Exporta la query a CSV en /tmp por trozos y sube a S3.
    SSCursor evita cargar toda la tabla en RAM (OOM en t3.micro).
    """
    timestamp = ts()
    local_file = f"/tmp/{name}_{timestamp}.csv"
    s3_key = f"raw/{name}/{name}_{timestamp}.csv"

    conn = _connect()
    wrote = False
    batches = 0

    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]

            with open(local_file, "w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(columns)

                while True:
                    rows = cursor.fetchmany(fetch_size)
                    if not rows:
                        break
                    writer.writerows(rows)
                    wrote = True
                    batches += 1
                    if batches % 20 == 0:
                        gc.collect()

        if not wrote:
            print(f"[WARN] No rows for table: {name}")
            if os.path.exists(local_file):
                os.remove(local_file)
            return

        print(f"[DB INGEST] {name}: {batches} batch(es) de {fetch_size} filas")
        upload_path(local_file, s3_key, "DB INGEST")
    except Exception:
        if os.path.exists(local_file):
            os.remove(local_file)
        raise
    finally:
        conn.close()
        gc.collect()
