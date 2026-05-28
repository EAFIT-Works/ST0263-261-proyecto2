from __future__ import annotations

import os

try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True), override=False)
except ImportError:
    pass


BUCKET = os.getenv("S3_BUCKET", "movie-analytics-lake2")

LOCAL_DATA_PATH = os.getenv("DATA_PATH", "/home/ubuntu/project/data")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "movies")
DB_FETCH_SIZE = int(os.getenv("DB_FETCH_SIZE", "1000"))
