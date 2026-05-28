import gc
import os

import ingest_api
import ingest_db
import ingest_ec2


def run_pipeline():
    print("=== FULL INGEST PIPELINE START ===")

    ingest_ec2.ingest_ec2_files()
    gc.collect()

    ingest_db.ingest_table(
        "SELECT * FROM people",
        "people",
        fetch_size=int(os.environ.get("PEOPLE_FETCH_SIZE", "1000")),
    )
    gc.collect()

    ingest_db.ingest_table(
        "SELECT * FROM movie_reviews",
        "movie_reviews",
        fetch_size=int(os.environ.get("REVIEWS_FETCH_SIZE", "200")),
    )
    gc.collect()

    ingest_api.ingest_api()

    print("=== FULL INGEST PIPELINE END ===")


if __name__ == "__main__":
    run_pipeline()