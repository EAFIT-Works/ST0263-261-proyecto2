import os

BUCKET = "movie-analytics-lake"
LOCAL_DATA_PATH = "/home/ubuntu/project/data"
CHUNK_SIZE = int(os.environ.get("INGEST_CHUNK_SIZE", "5000"))

DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "admin123")
DB_HOST = os.environ.get("DB_HOST", "44.215.233.75")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ.get("DB_NAME", "movies")
