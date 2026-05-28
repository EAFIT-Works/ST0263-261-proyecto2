import gc
import os

import pandas as pd
from sqlalchemy import create_engine

from config import (
    CSV_CHUNK_SIZE,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    LOCAL_DATA_PATH,
)

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
                        pool_pre_ping=True, pool_size=1, max_overflow=0,)


def load_csv(file_name: str, table_name: str, chunksize: int = CSV_CHUNK_SIZE) -> None:
    path = os.path.join(LOCAL_DATA_PATH, file_name)
    print(f"[LOADING] {file_name} -> {table_name}")

    first = True
    for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=True):
        chunk.to_sql(
            name=table_name,
            con=engine,
            if_exists="replace" if first else "append",
            index=False,
            method="multi",
            chunksize=min(chunksize, 1000),
        )
        first = False
        del chunk
        gc.collect()

    print(f"[OK] {table_name} loaded")


if __name__ == "__main__":
    print("=== START LOADING INTO MARIADB ===")
    load_csv("people.csv", "people")
    gc.collect()
    load_csv("movie_reviews.csv", "movie_reviews")
    print("=== DONE ===")