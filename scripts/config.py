import os

BUCKET = os.environ.get("S3_BUCKET", "movie-analytics-lake2")
LOCAL_DATA_PATH = "/home/ubuntu/project/data"

# Filas por fetch desde MariaDB (t3.micro: 200–500 suele ir bien)
DB_FETCH_SIZE = int(os.environ.get("DB_FETCH_SIZE", "500"))
# Carga CSV -> MariaDB (load_db_data.py)
CSV_CHUNK_SIZE = int(os.environ.get("CSV_CHUNK_SIZE", "2000"))

DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "admin123")
DB_HOST = os.environ.get("DB_HOST", "44.215.233.75")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ.get("DB_NAME", "movies")
