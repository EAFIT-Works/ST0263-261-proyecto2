import datetime
import gc
import os

import pandas as pd
from sqlalchemy import create_engine

from config import (
    CHUNK_SIZE,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)
from s3_util import upload_path

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
)


def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def ingest_table(query: str, name: str, chunksize: int = CHUNK_SIZE) -> None:
    timestamp = ts()
    local_file = f"/tmp/{name}_{timestamp}.csv"
    s3_key = f"raw/{name}/{name}_{timestamp}.csv"

    wrote = False
    try:
        for i, chunk in enumerate(pd.read_sql(query, engine, chunksize=chunksize)):
            chunk.to_csv(
                local_file,
                index=False,
                mode="w" if i == 0 else "a",
                header=(i == 0),
            )
            del chunk
            wrote = True
            if i % 10 == 0:
                gc.collect()

        if not wrote:
            print(f"[WARN] No rows for table: {name}")
            return

        upload_path(local_file, s3_key, "DB INGEST")
    except Exception:
        if os.path.exists(local_file):
            os.remove(local_file)
        raise
