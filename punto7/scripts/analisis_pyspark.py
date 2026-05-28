import sys
from typing import Iterable

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def _arg(name, default):
    flag = f"--{name}"
    if flag in sys.argv:
        return sys.argv[sys.argv.index(flag) + 1]
    return default

args = getResolvedOptions(sys.argv, ["JOB_NAME"])

TRUSTED = _arg("TRUSTED_PREFIX", "s3://movie-analytics-lake2/trusted/").rstrip("/") + "/"
CURATED = _arg("CURATED_PREFIX", "s3://movie-analytics-lake2/curated/").rstrip("/") + "/"
SAMPLE_SIZE = int(_arg("SAMPLE_SIZE", "2000"))
DECADE_FROM = int(_arg("DECADE_FROM", "1980"))
MIN_DIR_MOVIES = int(_arg("MIN_DIR_MOVIES", "3"))

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
spark.conf.set("spark.sql.session.timeZone", "UTC")
spark.conf.set("spark.sql.parquet.compression.codec", "snappy")
spark.sparkContext.setLogLevel("WARN")

job = Job(glueContext)
job.init(args["JOB_NAME"], args)


def read_trusted(name: str) -> DataFrame:

    path = f"{TRUSTED}{name}/"
    print(f"[READ] {path}")
    return spark.read.parquet(path)


def write_curated(df: DataFrame, name: str, partition_by: Iterable[str] = ()) -> None:

    path = f"{CURATED}{name}/"
    n = df.count()
    print(f"[WRITE] {path}  ({n:,} filas)")
    writer = df.write.mode("overwrite")
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    writer.parquet(path)


def show_top(df: DataFrame, n: int = 20, title: str = "") -> None:
    if title:
        print(f"\n----- {title} -----")
    df.show(n=n, truncate=False)

def revenue_by_genre(movies: DataFrame, movie_genres: DataFrame) -> DataFrame:
    movies_fin = movies.where(
        F.col("revenue_usd").isNotNull()
        & F.col("revenue_cop").isNotNull()
        & (F.col("revenue_usd") > 0)
    ).select("tmdb_id", "revenue_usd", "revenue_cop")

    joined = movie_genres.alias("g").join(
        movies_fin.alias("m"), on="tmdb_id", how="inner"
    )
    return (
        joined.groupBy("genre")
        .agg(
            F.countDistinct("tmdb_id").alias("n_movies"),
            F.round(F.sum("revenue_usd"), 2).alias("revenue_usd_total"),
            F.round(F.avg("revenue_usd"), 2).alias("revenue_usd_avg"),
            F.round(F.sum("revenue_cop"), 2).alias("revenue_cop_total"),
            F.round(F.avg("revenue_cop"), 2).alias("revenue_cop_avg"),
        )
        .orderBy(F.desc("revenue_usd_total"))
    )


def top_actors_rentables(movies: DataFrame, people: DataFrame) -> DataFrame:
    rentables = movies.where(
        F.col("profit_usd").isNotNull()
        & (F.col("profit_usd") > 0)
        & F.col("cast_ids").isNotNull()
        & (F.trim(F.col("cast_ids")) != "")
    ).select("tmdb_id", "profit_usd", "revenue_usd", "cast_ids")

    actors_per_movie = (
        rentables.withColumn(
            "actor_id_raw", F.explode(F.split(F.col("cast_ids"), ","))
        )
        .withColumn("actor_id", F.trim(F.col("actor_id_raw")).cast("integer"))
        .where(F.col("actor_id").isNotNull())
        .select("tmdb_id", "profit_usd", "revenue_usd", "actor_id")
    )

    joined = actors_per_movie.alias("a").join(
        people.alias("p"),
        F.col("a.actor_id") == F.col("p.tmdb_id"),
        how="inner",
    )

    return (
        joined.groupBy(F.col("p.tmdb_id").alias("actor_id"), F.col("p.name").alias("actor_name"))
        .agg(
            F.countDistinct("a.tmdb_id").alias("n_movies_rentables"),
            F.round(F.avg("a.profit_usd"), 2).alias("avg_profit_usd"),
            F.round(F.sum("a.revenue_usd"), 2).alias("total_revenue_usd"),
        )
        .orderBy(F.desc("n_movies_rentables"), F.desc("avg_profit_usd"))
        .limit(25)
    )


def revenue_by_year(movies: DataFrame) -> DataFrame:
    return (
        movies.where(
            F.col("release_year").isNotNull()
            & (F.col("release_year") >= DECADE_FROM)
            & F.col("revenue_usd").isNotNull()
            & F.col("revenue_cop").isNotNull()
        )
        .groupBy("release_year")
        .agg(
            F.count("*").alias("n_movies"),
            F.round(F.sum("revenue_usd"), 2).alias("revenue_usd_total"),
            F.round(F.sum("revenue_cop"), 2).alias("revenue_cop_total"),
            F.round(F.avg("roi_pct"), 2).alias("avg_roi_pct"),
        )
        .where(F.col("n_movies") >= 5)
        .orderBy("release_year")
    )


def roi_by_director(movies: DataFrame) -> DataFrame:
    with_dirs = movies.where(F.col("directors").isNotNull() & (F.trim(F.col("directors")) != "") & F.col("roi_pct").isNotNull()).select("tmdb_id", "directors", "roi_pct", "profit_usd", "revenue_usd")
    by_director = with_dirs.withColumn("director_raw", F.explode(F.split(F.col("directors"), ","))).withColumn("director_name", F.trim(F.col("director_raw"))).where(F.col("director_name") != "")
    return (by_director.groupBy("director_name").agg(F.countDistinct("tmdb_id").alias("n_movies"), F.round(F.avg("roi_pct"), 2).alias("avg_roi_pct"), F.round(F.avg("profit_usd"), 2).alias("avg_profit_usd"), F.round(F.sum("revenue_usd"), 2).alias("total_revenue_usd")).where(F.col("n_movies") >= MIN_DIR_MOVIES).orderBy(F.desc("avg_roi_pct")).limit(20))

def ratings_correlations(movies: DataFrame, movie_reviews: DataFrame) -> DataFrame:
    review_agg = movie_reviews.where(F.col("rating").isNotNull()).groupBy("tmdb_id").agg(F.avg("rating").alias("avg_review_rating"), F.count("*").alias("n_reviews")).where(F.col("n_reviews") >= 3).select("tmdb_id", "avg_review_rating")

    base = movies.where(F.col("vote_average").isNotNull() & F.col("revenue_usd").isNotNull() & (F.col("revenue_usd") > 0)).select("tmdb_id", "title", "vote_average", "revenue_usd", "profit_usd").join(review_agg, on="tmdb_id", how="left")
    return base.agg(F.round(F.corr("vote_average", "revenue_usd"), 4).alias("corr_tmdb_revenue"), F.round(F.corr("vote_average", "profit_usd"), 4).alias("corr_tmdb_profit"), F.round(F.corr("vote_average", "roi_pct"), 4).alias("corr_tmdb_roi"), F.round(F.corr("avg_review_rating", "revenue_usd"), 4).alias("corr_reviews_revenue"), F.round(F.corr("avg_review_rating", "profit_usd"), 4).alias("corr_reviews_profit"), F.round(F.corr("avg_review_rating", "roi_pct"), 4).alias("corr_reviews_roi"))


def ratings_vs_revenue_sample(movies: DataFrame, movie_reviews: DataFrame) -> DataFrame:
    review_agg = movie_reviews.where(F.col("rating").isNotNull()).groupBy("tmdb_id").agg(F.round(F.avg("rating"), 2).alias("avg_review_rating"), F.count("*").alias("n_reviews")).where(F.col("n_reviews") >= 3).select("tmdb_id", "avg_review_rating")

    base = movies.where(F.col("vote_average").isNotNull() & F.col("revenue_usd").isNotNull() & (F.col("revenue_usd") > 0)).select("tmdb_id", "title", "vote_average", "revenue_usd", "profit_usd").join(review_agg, on="tmdb_id", how="left")

    total = base.count()
    fraction = min(1.0, SAMPLE_SIZE * 1.2 / total) if total > 0 else 1.0
    return base.sample(fraction=fraction, seed=42).limit(SAMPLE_SIZE)


print(f"\nLectura desde {TRUSTED}")
movies = read_trusted("movies")
movie_genres = read_trusted("movie_genres")
people = read_trusted("people")
movie_reviews = read_trusted("movie_reviews")

df_revenue_by_genre = revenue_by_genre(movies, movie_genres)
show_top(df_revenue_by_genre, 20, "Q1 — Géneros más rentables")
write_curated(df_revenue_by_genre, "revenue_by_genre")

df_top_actors = top_actors_rentables(movies, people)
show_top(df_top_actors, 25, "Q2 — Top actores en películas rentables")
write_curated(df_top_actors, "top_actors_rentables")

df_revenue_by_year = revenue_by_year(movies)
show_top(df_revenue_by_year, 50, "Q3 — Revenue por año (desde DECADE_FROM)")
write_curated(df_revenue_by_year, "revenue_by_year")

df_roi_by_director = roi_by_director(movies)
show_top(df_roi_by_director, 20, "Q4 — Top directores por ROI")
write_curated(df_roi_by_director, "roi_by_director")

df_correlations = ratings_correlations(movies, movie_reviews)
show_top(df_correlations, 1, "Q5a — Correlaciones rating vs ganancias")
write_curated(df_correlations, "ratings_correlations")

df_sample = ratings_vs_revenue_sample(movies, movie_reviews)
show_top(df_sample, 10, "Q5b — Sample rating vs revenue (primeras 10)")
write_curated(df_sample, "ratings_vs_revenue_sample")

print(f"\n[OK] Punto 7 finalizado. Zona curated/ poblada en {CURATED}")

job.commit()