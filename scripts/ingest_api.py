import requests
import boto3
import pandas as pd
import datetime

BUCKET = "movie-analytics-lake"
API_URL = "https://api.exchangerate-api.com/v4/latest/USD"

s3 = boto3.client("s3")


def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def fetch_api():
    response = requests.get(API_URL)
    return response.json()


def transform(data):
    rates = data["rates"]

    df = pd.DataFrame(list(rates.items()), columns=["currency", "rate"])
    df["base"] = data["base"]
    df["date"] = data["date"]

    return df


def upload_to_s3(df):
    timestamp = ts()

    local_file = f"/tmp/exchange_{timestamp}.csv"
    s3_key = f"raw/exchange/exchange_{timestamp}.csv"

    df.to_csv(local_file, index=False)
    s3.upload_file(local_file, BUCKET, s3_key)

    print(f"[API INGEST] Uploaded: s3://{BUCKET}/{s3_key}")


def ingest_api():
    print("=== API INGEST START ===")

    data = fetch_api()
    df = transform(data)
    upload_to_s3(df)

    print("=== API INGEST END ===")
