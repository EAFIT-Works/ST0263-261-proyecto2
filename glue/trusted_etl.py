"""Raw CSV on S3 to cleaned Parquet under trusted/. Overwrites each table prefix."""

import sys

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    desc,
    explode,
    lit,
    lower,
    row_number,
    split,
    trim,
    upper,
    when,
)
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StringType,
)
from pyspark.sql.window import Window

DEFAULT_ARGS = {
    "JOB_NAME": "cinegraph-trusted-etl",
    "RAW_PREFIX": "s3://movie-analytics-lake2/raw/",
    "TRUSTED_PREFIX": "s3://movie-analytics-lake2/trusted/",
    "REFERENCE_CURRENCY": "COP",
}

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "RAW_PREFIX", "TRUSTED_PREFIX", "REFERENCE_CURRENCY"],
)

for key, default in DEFAULT_ARGS.items():
    args.setdefault(key, default)

RAW = args["RAW_PREFIX"].rstrip("/") + "/"
TRUSTED = args["TRUSTED_PREFIX"].rstrip("/") + "/"
REF_CURRENCY = args["REFERENCE_CURRENCY"].upper()

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args["JOB_NAME"], args)

def read_csv(path: str) -> DataFrame:
    return (
        glueContext.create_dynamic_frame.from_options(
            connection_type="s3",
            connection_options={"paths": [path]},
            format="csv",
            format_options={"withHeader": True},
        )
        .toDF()
    )


movies = read_csv(f"{RAW}movies/")
tv = read_csv(f"{RAW}tv_shows/")
people = read_csv(f"{RAW}people/")
movie_reviews = read_csv(f"{RAW}movie_reviews/")
tv_reviews = read_csv(f"{RAW}tv_reviews/")
orphan_movies = read_csv(f"{RAW}orphan_movies/")
orphan_tv = read_csv(f"{RAW}orphan_tv/")
exchange = read_csv(f"{RAW}exchange/")

# Treat empty strings and literal "null" from the CSV export as SQL null.
NULL_LIKE = ("", "null", "NULL", "None", "nan", "NaN")


def _nullify_strings(df: DataFrame, columns: list[str]) -> DataFrame:
    for name in columns:
        if name not in df.columns:
            continue
        cleaned = trim(col(name).cast(StringType()))
        df = df.withColumn(
            name,
            when(cleaned.isin(*NULL_LIKE), lit(None)).otherwise(cleaned),
        )
    return df


def _trim_strings(df: DataFrame, columns: list[str]) -> DataFrame:
    for name in columns:
        if name not in df.columns:
            continue
        df = df.withColumn(name, trim(col(name).cast(StringType())))
    return df


def _to_int(df: DataFrame, columns: list[str]) -> DataFrame:
    for name in columns:
        if name not in df.columns:
            continue
        df = df.withColumn(name, col(name).cast(IntegerType()))
    return df


def _to_double(df: DataFrame, columns: list[str]) -> DataFrame:
    for name in columns:
        if name not in df.columns:
            continue
        df = df.withColumn(name, col(name).cast(DoubleType()))
    return df


def _to_bool(df: DataFrame, columns: list[str]) -> DataFrame:
    for name in columns:
        if name not in df.columns:
            continue
        raw = lower(trim(col(name).cast(StringType())))
        df = df.withColumn(
            name,
            when(raw.isin("true", "1", "yes"), lit(True))
            .when(raw.isin("false", "0", "no"), lit(False))
            .otherwise(lit(None).cast(BooleanType())),
        )
    return df


def prepare_movies(df: DataFrame) -> DataFrame:
    df = _nullify_strings(
        df,
        [
            "imdb_id",
            "title",
            "original_title",
            "original_language",
            "tagline",
            "overview",
            "release_date",
            "status",
            "genres",
            "keywords",
            "us_certification",
            "collection_name",
        ],
    )
    df = _to_int(
        df,
        [
            "tmdb_id",
            "release_year",
            "runtime_min",
            "vote_count",
            "collection_id",
        ],
    )
    df = _to_double(
        df,
        [
            "vote_average",
            "popularity",
            "budget_usd",
            "revenue_usd",
        ],
    )
    df = _to_bool(df, ["has_trailer"])
    return df.withColumn("genres", lower(col("genres")))


def prepare_tv(df: DataFrame) -> DataFrame:
    df = _nullify_strings(
        df,
        [
            "imdb_id",
            "title",
            "original_title",
            "original_language",
            "tagline",
            "overview",
            "first_air_date",
            "last_air_date",
            "status",
            "show_type",
            "genres",
            "keywords",
            "cert_tr",
            "cert_us",
        ],
    )
    df = _to_int(
        df,
        [
            "tmdb_id",
            "tvdb_id",
            "release_year",
            "number_of_seasons",
            "number_of_episodes",
            "avg_episode_runtime",
            "season_count",
            "vote_count",
        ],
    )
    df = _to_double(df, ["vote_average", "popularity"])
    df = _to_bool(df, ["in_production"])
    return df.withColumn("genres", lower(col("genres")))


def prepare_people(df: DataFrame) -> DataFrame:
    df = _nullify_strings(
        df,
        [
            "imdb_id",
            "instagram_id",
            "twitter_id",
            "name",
            "gender",
            "birthday",
            "deathday",
            "place_of_birth",
            "known_for_dept",
            "homepage",
        ],
    )
    df = _to_int(
        df,
        ["tmdb_id", "total_movie_credits", "total_directed", "total_tv_credits"],
    )
    return _to_double(df, ["popularity"])


def prepare_reviews(df: DataFrame) -> DataFrame:
    df = _nullify_strings(
        df,
        ["review_id", "author", "content", "created_at", "url", "media_type"],
    )
    df = _to_int(df, ["tmdb_id"])
    return _to_double(df, ["rating"])


def prepare_orphan_movies(df: DataFrame) -> DataFrame:
    df = _nullify_strings(
        df,
        ["imdb_id", "title", "original_language", "overview", "genres"],
    )
    df = _to_int(df, ["tmdb_id", "release_year", "vote_count"])
    df = _to_double(df, ["vote_average"])
    return df.withColumn("genres", lower(col("genres")))


def prepare_orphan_tv(df: DataFrame) -> DataFrame:
    df = _nullify_strings(
        df, ["title", "original_language", "overview", "genres"]
    )
    df = _to_int(df, ["tmdb_id", "release_year", "vote_count"])
    df = _to_double(df, ["vote_average"])
    return df.withColumn("genres", lower(col("genres")))


def prepare_exchange(df: DataFrame) -> DataFrame:
    df = _trim_strings(df, ["currency"])
    df = _to_double(df, ["rate"])
    return df.withColumn("currency", upper(col("currency")))


movies = prepare_movies(movies)
tv = prepare_tv(tv)
people = prepare_people(people)
movie_reviews = prepare_reviews(movie_reviews)
tv_reviews = prepare_reviews(tv_reviews)
orphan_movies = prepare_orphan_movies(orphan_movies)
orphan_tv = prepare_orphan_tv(orphan_tv)
exchange = prepare_exchange(exchange)

def keep_best_row(
    df: DataFrame,
    key: str,
    order_cols: list[str],
) -> DataFrame:
    window = Window.partitionBy(key).orderBy(
        *[desc(c) for c in order_cols]
    )
    return (
        df.withColumn("_rn", row_number().over(window))
        .filter(col("_rn") == 1)
        .drop("_rn")
    )


movies = keep_best_row(
    movies,
    "tmdb_id",
    ["release_year", "vote_count", "popularity"],
)
tv = keep_best_row(
    tv,
    "tmdb_id",
    ["release_year", "vote_count", "popularity"],
)

people = keep_best_row(people, "tmdb_id", ["popularity"])

movie_reviews = keep_best_row(movie_reviews, "review_id", ["created_at"])
tv_reviews = keep_best_row(tv_reviews, "review_id", ["created_at"])

exchange = exchange.dropDuplicates(["currency"])

movies = movies.withColumn(
    "profit_usd",
    when(
        col("revenue_usd").isNotNull() & col("budget_usd").isNotNull(),
        col("revenue_usd") - col("budget_usd"),
    ),
).withColumn(
    "roi_pct",
    when(
        col("budget_usd").isNotNull() & (col("budget_usd") > 0),
        (col("revenue_usd") / col("budget_usd")) * 100,
    ),
)

fx_ref = (
    exchange.filter(col("currency") == REF_CURRENCY)
    .select(col("rate").alias("_fx_rate"))
    .limit(1)
)

if fx_ref.head() is None:
    fx_rate = lit(1.0)
else:
    fx_rate = fx_ref.collect()[0]["_fx_rate"]

movies = movies.withColumn(
    f"revenue_{REF_CURRENCY.lower()}",
    col("revenue_usd") * lit(fx_rate),
)

tv = tv.withColumn(
    "popularity_bucket",
    when(col("popularity") > 300, "high")
    .when(col("popularity") > 100, "medium")
    .otherwise("low"),
)

movies = movies.withColumn(
    "decade",
    when(col("release_year").isNotNull(), (col("release_year") / 10).cast("int") * 10),
)

tv = tv.withColumn(
    "decade",
    when(col("release_year").isNotNull(), (col("release_year") / 10).cast("int") * 10),
)


def explode_genres(df: DataFrame, id_col: str = "tmdb_id") -> DataFrame:
    base = df.filter(col("genres").isNotNull() & (col("genres") != ""))
    return (
        base.withColumn("genre", explode(split(col("genres"), ",")))
        .withColumn("genre", trim(col("genre")))
        .filter(col("genre") != "")
        .select(id_col, "genre")
    )


movie_genres = explode_genres(movies)
tv_genres = explode_genres(tv)

# Drop reviews whose tmdb_id is not in the deduped movie/tv set.
valid_movie_ids = movies.select("tmdb_id").distinct()
valid_tv_ids = tv.select("tmdb_id").distinct()

movie_reviews = movie_reviews.join(valid_movie_ids, "tmdb_id", "inner")
tv_reviews = tv_reviews.join(valid_tv_ids, "tmdb_id", "inner")

def write_single_parquet(df: DataFrame, path: str) -> None:
    target = path.rstrip("/") + "/"
    (
        df.coalesce(1)
        .write.mode("overwrite")
        .option("compression", "snappy")
        .parquet(target)
    )


write_single_parquet(movies, f"{TRUSTED}movies")
write_single_parquet(movie_genres, f"{TRUSTED}movie_genres")
write_single_parquet(tv, f"{TRUSTED}tv_shows")
write_single_parquet(tv_genres, f"{TRUSTED}tv_genres")
write_single_parquet(people, f"{TRUSTED}people")
write_single_parquet(movie_reviews, f"{TRUSTED}movie_reviews")
write_single_parquet(tv_reviews, f"{TRUSTED}tv_reviews")
write_single_parquet(orphan_movies, f"{TRUSTED}orphan_movies")
write_single_parquet(orphan_tv, f"{TRUSTED}orphan_tv")
write_single_parquet(exchange, f"{TRUSTED}exchange")

job.commit()
