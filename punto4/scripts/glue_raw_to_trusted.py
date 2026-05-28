import sys

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    broadcast,
    coalesce,
    col,
    desc,
    explode,
    length,
    lit,
    lower,
    regexp_replace,
    row_number,
    split,
    trim,
    upper,
    when,
)

from pyspark.sql.types import BooleanType, DoubleType, IntegerType, StringType
from pyspark.sql.window import Window


def _arg(name, default):
    flag = f"--{name}"
    if flag in sys.argv:
        return sys.argv[sys.argv.index(flag) + 1]
    return default

args = getResolvedOptions(sys.argv, ["JOB_NAME"])
RAW = _arg("RAW_PREFIX", "s3://movie-analytics-lake2/raw/").rstrip("/") + "/"
TRUSTED = _arg("TRUSTED_PREFIX", "s3://movie-analytics-lake2/trusted/").rstrip("/") + "/"

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(args["JOB_NAME"], args)

NULL_LIKE = ("", "null", "NULL", "None", "nan", "NaN", "N/A", "n/a")


def read_csv(path):
    return glueContext.create_dynamic_frame.from_options(connection_type="s3", connection_options={"paths": [path]}, format="csv", format_options={"withHeader": True}).toDF()

def nullify(df, *cols):
    for name in cols:
        if name not in df.columns:
            continue
        s = trim(col(name).cast(StringType()))
        df = df.withColumn(
            name, when(s.isin(*NULL_LIKE), lit(None)).otherwise(s)
        )
    return df


def cast_int(df, *cols):
    for name in cols:
        if name in df.columns:
            df = df.withColumn(name, col(name).cast(IntegerType()))
    return df


def cast_double(df, *cols):
    for name in cols:
        if name in df.columns:
            df = df.withColumn(name, col(name).cast(DoubleType()))
    return df


def cast_bool(df, *cols):
    for name in cols:
        if name not in df.columns:
            continue
        raw = lower(trim(col(name).cast(StringType())))
        df = df.withColumn(
            name,
            when(raw.isin("true", "1", "yes"), lit(True)).when(raw.isin("false", "0", "no"), lit(False)).otherwise(lit(None).cast(BooleanType()))
        )
    return df


def normalize_genres(df):
    if "genres" not in df.columns:
        return df
    g = lower(trim(col("genres")))
    g = regexp_replace(g, r"\s*,\s*", ", ")
    g = regexp_replace(g, r",\s*,", ", ")
    return df.withColumn(
        "genres",
        when(g.isin(*NULL_LIKE), lit(None)).otherwise(g),
    )

def drop_bad_ids(df, key="tmdb_id"):
    return df.filter(col(key).isNotNull() & (col(key) > 0))

def keep_one(df, key, *order_by):
    w = Window.partitionBy(key).orderBy(*[desc(c) for c in order_by])
    return (
        df.withColumn("_rn", row_number().over(w))
        .filter(col("_rn") == 1)
        .drop("_rn")
    )

movies = read_csv(f"{RAW}movies/")
tv = read_csv(f"{RAW}tv_shows/")
people = read_csv(f"{RAW}people/")
reviews = read_csv(f"{RAW}movie_reviews/")
exchange = read_csv(f"{RAW}exchange/")

movies = nullify(
    movies,
    "imdb_id",
    "title",
    "original_title",
    "original_language",
    "alternative_titles",
    "tagline",
    "overview",
    "release_date",
    "status",
    "genres",
    "keywords",
    "us_certification",
    "production_companies",
    "production_countries",
    "spoken_languages",
    "collection_name",
    "cast_names",
    "cast_ids",
    "cast_characters",
    "directors",
    "director_ids",
    "writers",
    "producers",
    "composers",
    "trailer_url",
    "similar_ids",
    "similar_titles",
    "recommended_ids",
    "recommended_titles",
    "poster_url",
    "poster_url_hd",
    "backdrop_url",
    "homepage",
    "watch_tr_flatrate",
    "watch_tr_rent",
    "watch_tr_buy",
    "watch_tr_free",
    "watch_tr_link",
    "watch_us_flatrate",
    "watch_us_rent",
    "watch_us_buy",
    "watch_us_free",
    "watch_us_link",
)

movies = cast_int(
    movies,
    "tmdb_id",
    "release_year",
    "runtime_min",
    "vote_count",
    "collection_id",
)
movies = cast_double(
    movies,
    "vote_average",
    "popularity",
    "budget_usd",
    "revenue_usd",
)
movies = cast_bool(movies, "has_trailer")
movies = normalize_genres(movies)
movies = drop_bad_ids(movies)

movies = movies.withColumn(
    "budget_usd",
    when(col("budget_usd") < 0, lit(None)).otherwise(col("budget_usd")),
).withColumn(
    "revenue_usd",
    when(col("revenue_usd") < 0, lit(None)).otherwise(col("revenue_usd")),
)

movies = keep_one(movies, "tmdb_id", "release_year", "vote_count", "popularity")

tv = nullify(
    tv,
    "imdb_id",
    "title",
    "original_title",
    "original_language",
    "alternative_titles",
    "tagline",
    "overview",
    "first_air_date",
    "last_air_date",
    "status",
    "show_type",
    "genres",
    "keywords",
    "networks",
    "network_ids",
    "origin_countries",
    "spoken_languages",
    "production_companies",
    "creators",
    "creator_ids",
    "cast_names",
    "cast_ids",
    "cast_characters",
    "writers",
    "similar_ids",
    "similar_titles",
    "recommended_ids",
    "recommended_titles",
    "poster_url",
    "poster_url_hd",
    "backdrop_url",
    "homepage",
    "watch_tr_flatrate",
    "watch_tr_rent",
    "watch_tr_buy",
    "watch_tr_free",
    "watch_tr_link",
    "watch_us_flatrate",
    "watch_us_rent",
    "watch_us_buy",
    "watch_us_free",
    "watch_us_link",
    "cert_tr",
    "cert_us",
)

tv = cast_int(
    tv,
    "tmdb_id",
    "tvdb_id",
    "release_year",
    "number_of_seasons",
    "number_of_episodes",
    "avg_episode_runtime",
    "season_count",
    "vote_count",
)
tv = cast_double(tv, "vote_average", "popularity")
tv = cast_bool(tv, "in_production")
tv = normalize_genres(tv)
tv = drop_bad_ids(tv)
tv = keep_one(tv, "tmdb_id", "release_year", "vote_count", "popularity")

tv = tv.withColumn(
    "popularity_bucket",
    when(col("popularity") > 300, "high")
    .when(col("popularity") > 100, "medium")
    .otherwise("low"),
)

people = nullify(
    people,
    "imdb_id",
    "instagram_id",
    "twitter_id",
    "name",
    "also_known_as",
    "gender",
    "birthday",
    "deathday",
    "place_of_birth",
    "known_for_dept",
    "biography",
    "known_movies",
    "known_movie_ids",
    "directed_movies",
    "directed_movie_ids",
    "known_tv_shows",
    "known_tv_ids",
    "profile_url",
    "homepage",
)

people = cast_int(
    people,
    "tmdb_id",
    "total_movie_credits",
    "total_directed",
    "total_tv_credits",
)
people = cast_double(people, "popularity")
people = drop_bad_ids(people)
people = keep_one(people, "tmdb_id", "popularity", "total_movie_credits")


reviews = nullify(
    reviews,
    "review_id",
    "author",
    "content",
    "created_at",
    "url",
    "media_type",
)

reviews = cast_int(reviews, "tmdb_id")
reviews = cast_double(reviews, "rating")

reviews = reviews.withColumn(
    "rating",
    when(
        col("rating").isNotNull()
        & ((col("rating") < 0) | (col("rating") > 10)),
        lit(None),
    ).otherwise(col("rating")),
)

reviews = reviews.filter(
    col("review_id").isNotNull() & (length(col("review_id")) > 0)
)
reviews = keep_one(reviews, "review_id", "created_at")

movie_ids = movies.select("tmdb_id").distinct()
reviews = reviews.join(movie_ids, "tmdb_id", "inner")

exchange = nullify(exchange, "currency")
exchange = cast_double(exchange, "rate")
exchange = exchange.withColumn("currency", upper(trim(col("currency"))))
exchange = exchange.filter(
    col("currency").isNotNull() & col("rate").isNotNull() & (col("rate") > 0)
)
exchange = keep_one(exchange, "currency", "rate")


for _col in ("profit_usd", "roi_pct"):
    if _col in movies.columns:
        movies = movies.drop(_col)

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

cop = (
    exchange.filter(col("currency") == "COP")
    .select(coalesce(col("rate"), lit(1.0)).alias("_rate"))
    .limit(1)
)

if cop.take(1):
    movies = (
        movies.crossJoin(broadcast(cop))
        .withColumn("revenue_cop", col("revenue_usd") * col("_rate"))
        .drop("_rate")
    )
else:
    movies = movies.withColumn("revenue_cop", col("revenue_usd") * lit(1.0))

movies_genres = (
    movies.filter(col("genres").isNotNull())
    .withColumn("genre", explode(split(col("genres"), ",")))
    .withColumn("genre", trim(col("genre")))
    .filter(col("genre") != "")
    .select("tmdb_id", "genre")
)

def write(df, path):
    dyf = DynamicFrame.fromDF(df, glueContext, "dyf")
    glueContext.write_dynamic_frame.from_options(
        frame=dyf,
        connection_type="s3",
        connection_options={"path": path},
        format="parquet",
    )

write(movies, f"{TRUSTED}movies/")
write(movies_genres, f"{TRUSTED}movie_genres/")
write(tv, f"{TRUSTED}tv_shows/")
write(people, f"{TRUSTED}people/")
write(reviews, f"{TRUSTED}movie_reviews/")
write(exchange, f"{TRUSTED}exchange/")

job.commit()