import pandas as pd
from sqlalchemy import create_engine

# =========================
# CONFIG
# =========================

DB_USER = "admin"
DB_PASSWORD = "admin123"
DB_HOST = "54.146.173.72"
DB_PORT = 3306
DB_NAME = "movies"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

DATA_PATH = "/home/ubuntu/project/data"


# =========================
# FUNCTION
# =========================

def load_csv(file_name, table_name):
    path = f"{DATA_PATH}/{file_name}"

    print(f"[LOADING] {file_name} -> {table_name}")

    df = pd.read_csv(path)

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",
        index=False
    )

    print(f"[OK] {table_name} loaded")


# =========================
# RUN
# =========================

print("=== START LOADING INTO MARIADB===")

load_csv("people.csv", "people")
load_csv("movie_reviews.csv", "movie_reviews")

print("=== DONE ===")
