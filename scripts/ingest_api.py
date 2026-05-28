import csv
import datetime
import io

import requests

from s3_util import upload_bytes

API_URL = "https://api.exchangerate-api.com/v4/latest/USD"


def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def rates_to_csv_bytes(data: dict) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["currency", "rate", "base", "date"])
    base = data["base"]
    date = data["date"]
    for currency, rate in data["rates"].items():
        writer.writerow([currency, rate, base, date])
    return buf.getvalue().encode("utf-8")


def ingest_api():
    print("=== API INGEST START ===")

    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    body = rates_to_csv_bytes(response.json())

    timestamp = ts()
    s3_key = f"raw/exchange/exchange_{timestamp}.csv"
    upload_bytes(body, s3_key, "API INGEST")

    print("=== API INGEST END ===")
