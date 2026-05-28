# Cinegraph - Movie analytics pipeline

This project moves movie-related data from operational sources into S3, cleans and models it with AWS Glue, and answers business questions with Athena or PySpark.

## How the pipeline fits together

Data enters the lake from three places, all orchestrated on an **EC2** instance. Local CSV files (`movies.csv`, `tv_shows.csv`) are uploaded as-is. Rows from **MariaDB** (`people`, `movie_reviews`) are exported in small batches and streamed to S3 so memory stays low on small instances. Daily **exchange rates** are fetched from a public API and stored as CSV. Every run writes a new timestamped file under `s3://<bucket>/raw/<dataset>/`.

The **raw** layer is append-only CSV. Nothing is transformed yet; it is the landing zone for ingest.

An **AWS Glue** Spark job (`glue/trusted_etl.py`) reads those raw files, applies typing, deduplication, and business rules (for example `profit_usd`, `roi_pct`, `revenue_cop`), and writes **Parquet** to `s3://<bucket>/trusted/<table>/`. That trusted layer is what analytics tools query.

**Athena** runs SQL in `queries/athena_queries.sql` against tables registered in the Glue Data Catalog (database `movie_trusted_db`). **PySpark** runs the same logic in `queries/pyspark_sql.ipynb`, typically after loading trusted Parquet into a Spark session (Colab or Glue notebook). Both paths answer the same five business questions.

**Default bucket:** `movie-analytics-lake2`.

---

## Repository layout

| Path | Purpose |
|------|---------|
| `data/` | Local CSV for movies and TV shows (EC2 ingest) |
| `scripts/` | Ingest pipeline and optional MariaDB load |
| `queries/athena_queries.sql` | Five business questions for Athena |
| `queries/pyspark_sql.ipynb` | Same analytics on trusted Parquet with PySpark |
| `glue/trusted_etl.py` | Glue job: raw CSV → trusted Parquet |

---

## 1. Data ingestion

Ingestion runs on **EC2** (for example t3.micro). Each run uploads timestamped CSV files to `s3://<bucket>/raw/<dataset>/`.

### Sources

| Source | Script | S3 prefix |
|--------|--------|-----------|
| Local `movies.csv`, `tv_shows.csv` in `data/` | `ingest_ec2.py` | `raw/movies/`, `raw/tv_shows/` |
| MariaDB tables `people`, `movie_reviews` | `ingest_db.py` | `raw/people/`, `raw/movie_reviews/` |
| Exchange rate API (USD base) | `ingest_api.py` | `raw/exchange/` |

### Run the full pipeline

```bash
cd ~/project
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cd scripts
export S3_BUCKET=movie-analytics-lake2
export REVIEWS_FETCH_SIZE=200
export PEOPLE_FETCH_SIZE=1000
python3 ingest_all.py
```

### Configuration (`scripts/config.py` or environment)

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_BUCKET` | `movie-analytics-lake2` | Target bucket |
| `DB_HOST` | `44.215.233.75` | MariaDB host |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | `admin` / `admin123` / `movies` | Database credentials |
| `REVIEWS_FETCH_SIZE` | `200` | Batch size for `movie_reviews` |
| `PEOPLE_FETCH_SIZE` | `1000` | Batch size for `people` |

The EC2 instance needs an **IAM role** (or credentials) with `s3:PutObject` on `raw/*`.

`ingest_db.py` streams query results directly to S3 without filling `/tmp`. On small instances, keep fetch sizes low; add swap if the process exits with `Killed` (OOM).

### One-time load into MariaDB

If `people` and `movie_reviews` start as CSV files in `data/`:

```bash
cd scripts
python3 load_db_data.py
```

### Scheduled ingest (cron)

```cron
0 * * * * cd /home/ubuntu/project/scripts && /home/ubuntu/project/venv/bin/python3 ingest_all.py >> /home/ubuntu/ingest.log 2>&1
```

---

## 2. AWS Glue (trusted layer)

After new files land in `raw/`, run the ETL job **`glue/trusted_etl.py`**.

### What the job does

- Reads CSV from `raw/` per dataset.
- Cleans types, placeholder null strings, duplicates, and applies business rules (`profit_usd`, `roi_pct`, `revenue_cop`, etc.).
- Writes **Parquet** to `trusted/` (see `glue/trusted_etl.py` for the full list), including `movies`, `movie_genres`, `people`, `movie_reviews`, `exchange`, `tv_shows`, and related TV/orphan datasets.

### Glue job setup

1. Upload `glue/trusted_etl.py` as the job script (or point the job at the repo file).
2. Job type: **Spark**, Python 3.
3. Job parameters:

   | Parameter | Example |
   |-----------|---------|
   | `--RAW_PREFIX` | `s3://movie-analytics-lake2/raw/` |
   | `--TRUSTED_PREFIX` | `s3://movie-analytics-lake2/trusted/` |

4. IAM role: read `raw/`, write `trusted/`.
5. Run after each ingest (manual schedule, cron, or EventBridge).

### Glue Data Catalog (for Athena)

Create or update tables in database `movie_trusted_db` on `s3://<bucket>/trusted/<table>/` as **Parquet** (Glue crawler or manual DDL).

---

## 3. Queries: Athena or PySpark

Both engines answer the same five business questions:

1. Genres with the highest revenue (USD and COP).
2. Actors appearing in profitable movies (`profit_usd > 0`).
3. COP revenue by release year and applied exchange rate.
4. Directors with the best ROI (including COP-adjusted ROI).
5. Correlation between ratings and financial metrics.

### Athena

1. Open **Amazon Athena**, database `movie_trusted_db`.
2. Use `queries/athena_queries.sql`.
3. Run **one question block at a time** (one `SELECT` per execution).
4. Athena syntax uses `CROSS JOIN UNNEST(SPLIT(...))`.

### PySpark

Notebook `queries/pyspark_sql.ipynb` (Colab or Glue):

1. Configure AWS credentials (temporary keys require `aws_session_token`).
2. Load trusted Parquet from S3 (download locally or read from S3 if the runtime supports it).
3. Register views: `movies`, `movie_genres`, `people`, `movie_reviews`, `exchange`.
4. Run SQL equivalent to `athena_queries.sql` (Spark uses `LATERAL VIEW explode` instead of `UNNEST`).

In Glue Studio you can also use `spark.sql(...)` after `createOrReplaceTempView` on each Parquet path.

---

## Typical development workflow

1. Refresh files in `data/` and reload MariaDB if needed (`load_db_data.py`).
2. **Ingest** on EC2: `python3 ingest_all.py` → new objects under `raw/`.
3. **Transform** in AWS: Glue job `trusted_etl.py` → Parquet under `trusted/`.
4. **Validate** in Athena (`athena_queries.sql`) or PySpark (`pyspark_sql.ipynb`).
5. Repeat ingest + Glue on a schedule; trusted tables reflect the latest ETL run.

---

## Dependencies

```bash
pip install -r requirements.txt
```

Ingest: `boto3`, `pandas`, `pymysql`, `requests`, `sqlalchemy`. The Glue job uses libraries provided by the AWS Glue runtime.
