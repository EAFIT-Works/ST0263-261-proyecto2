import gc

import ingest_api
import ingest_db
import ingest_ec2


def run_pipeline():
    print("=== FULL INGEST PIPELINE START ===")

    ingest_ec2.ingest_ec2_files()
    gc.collect()

    ingest_db.ingest_table("SELECT * FROM people", "people")
    gc.collect()

    ingest_db.ingest_table("SELECT * FROM movie_reviews", "movie_reviews")
    gc.collect()

    ingest_api.ingest_api()

    print("=== FULL INGEST PIPELINE END ===")


if __name__ == "__main__":
    run_pipeline()
