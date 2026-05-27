import ingest_ec2
import ingest_db
import ingest_api


def run_pipeline():
    print("=== FULL INGEST PIPELINE START ===")

    # EC2 files
    ingest_ec2.ingest_ec2_files()

    # MariaDB
    ingest_db.ingest_table("SELECT * FROM people", "people")
    ingest_db.ingest_table("SELECT * FROM movie_reviews", "movie_reviews")

    # API
    ingest_api.ingest_api()

    print("=== FULL INGEST PIPELINE END ===")


run_pipeline()
