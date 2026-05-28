# Cinegraph — Pipeline de análisis financiero de películas

**Universidad EAFIT** · ST0263 Tópicos Especiales en Telemática · 2026-1

Este proyecto mueve datos de películas desde fuentes operacionales hacia un
Data Lake en S3, los limpia y modela con AWS Glue + Apache Spark, los cataloga
con el Glue Data Catalog, responde 5 preguntas de negocio con Athena y
PySpark, y expone los resultados en un dashboard Streamlit publicado vía
API Gateway.

## Enlaces del proyecto

| Recurso | URL |
|---------|-----|
| Repositorio oficial | <https://github.com/EAFIT-Works/ST0263-261-proyecto2> |
| Video de sustentación | <https://drive.google.com/file/d/1D01IppYtNwMOkz4dhGvd3RCrR1eKDxP2/view?usp=sharing> |
| Informe del proyecto (PDF) | [`ST0263-261-proyecto2.pdf`](ST0263-261-proyecto2.pdf) |

---

## Caso de estudio

**Análisis financiero de películas usando múltiples fuentes de datos.**

La industria del entretenimiento reporta sus métricas financieras (presupuesto,
ingresos, ganancia, ROI) en USD, mientras los inversionistas y el público
latinoamericanos razonan en COP. El proyecto combina un catálogo de títulos
(películas y series), datos transaccionales de personas y reseñas, y tasas de
cambio en línea para responder preguntas sobre rentabilidad histórica. Las 5
preguntas de negocio y el esquema completo están en
[`punto1/PUNTO1.md`](punto1/PUNTO1.md).

---

## Cómo encaja todo el pipeline

Los datos entran al lake desde tres lugares, todos orquestados sobre una
instancia **EC2**. Los archivos CSV locales (`movies.csv`, `tv_shows.csv`) se
suben tal cual. Las filas de **MariaDB** (`people`, `movie_reviews`) se
exportan en lotes pequeños y se transmiten directamente a S3 para que la
memoria de la EC2 no se llene. Las **tasas de cambio** diarias se consultan
desde una API pública y se guardan como CSV. Cada corrida escribe un archivo
nuevo con timestamp bajo `s3://<bucket>/raw/<dataset>/`.

La capa **`raw/`** es CSV append-only — nada se transforma, es solamente la
zona de aterrizaje del ingest.

Un **AWS Glue Job** Spark (`punto4/scripts/glue_raw_to_trusted.py`) lee esos
CSV, aplica tipado, deduplicación y reglas de negocio (por ejemplo
`profit_usd`, `roi_pct`, `revenue_cop`), y escribe **Parquet** en
`s3://<bucket>/trusted/<table>/`. Esa capa trusted es la que consumen las
herramientas analíticas.

**Athena** corre SQL sobre las tablas registradas en el Glue Data Catalog
(database `movie_trusted_db`). **PySpark** corre la misma lógica en
`punto6/queries/sparksql_queries.ipynb`, típicamente después de cargar el
Parquet trusted en una sesión Spark (Colab o Glue notebook). Ambos caminos
responden las mismas cinco preguntas de negocio.

Un segundo Glue Job (`punto7/scripts/analisis_pyspark.py`) toma la zona
trusted y materializa los resultados de las 5 preguntas en 6 tablas Parquet
dentro de **`curated/`**. Esas tablas son la fuente directa del dashboard
Streamlit (`punto8/app/`), desplegado en una segunda EC2 y publicado vía
**AWS API Gateway** (HTTP API).

**Bucket por defecto:** `movie-analytics-lake2` (región `us-east-1`).

---

## Estructura del repositorio

| Ruta | Contenido |
|------|-----------|
| `ST0263-261-proyecto2.pdf` | Informe consolidado del proyecto (documento oficial) |
| `punto1/` | Caso de estudio y preguntas de negocio (`PUNTO1.md`) |
| `punto2/scripts/` | Carga inicial de `people` y `movie_reviews` en MariaDB |
| `punto3/scripts/` | Ingesta automática: `ingest_ec2.py`, `ingest_db.py`, `ingest_api.py`, `ingest_all.py` |
| `punto4/scripts/glue_raw_to_trusted.py` | Glue Job: CSV `raw/` → Parquet `trusted/` |
| `punto5/evidencias/` | Capturas del Glue Crawler y la database `movie_trusted_db` |
| `punto6/queries/sparksql_queries.ipynb` | 5 consultas analíticas en SparkSQL (válidas también en Athena) |
| `punto7/scripts/analisis_pyspark.py` | Glue Job: Parquet `trusted/` → 6 tablas `curated/` |
| `punto8/app/` | Dashboard Streamlit (modular: `tabs/`, `data.py`, `styles.py`, etc.) |
| `data/` | CSVs locales para ingestar desde la EC2 |
| `requirements.txt` | Dependencias Python del pipeline (ingesta + dashboard) |

---

## Equipo

- Valentina Castro Pineda - vcastrop@eafit.edu.co
- Juan Pablo Avendaño Bustamante - jpavendanb@eafit.edu.co
- Diego Andres Gonzalez Graciano - dagonzal11@eafit.edu.co

---

## Configuración (`.env`)

Crear en la raíz un archivo `.env`copiando de `.env.example`:

```env
# RDS MariaDB
DB_HOST=<endpoint-rds>.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=<contraseña>
DB_NAME=movies

# Data Lake
S3_BUCKET=movie-analytics-lake2

# Archivos en el EC2
DATA_PATH=/home/ubuntu/project/data

# API externa
EXCHANGE_API_URL=https://api.exchangerate-api.com/v4/latest/USD
```
---

## 1. Ingesta de datos (Puntos 2 y 3)

La ingesta corre sobre **EC2** Ubuntu 22.04. Cada
corrida sube archivos CSV con timestamp a `s3://<bucket>/raw/<dataset>/`.

### Fuentes

| Fuente | Script | Prefijo S3 |
|--------|--------|------------|
| `movies.csv`, `tv_shows.csv` locales en `data/` | `punto3/scripts/ingest_ec2.py` | `raw/movies/`, `raw/tv_shows/` |
| Tablas MariaDB `people`, `movie_reviews` | `punto3/scripts/ingest_db.py` | `raw/people/`, `raw/movie_reviews/` |
| API de tasas de cambio (base USD) | `punto3/scripts/ingest_api.py` | `raw/exchange/` |

### Correr la ingesta completa

```bash
cd ~/project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd punto3/scripts
python3 ingest_all.py
```

### Carga inicial de la BD (una sola vez)

Si `people` y `movie_reviews` arrancan como CSV en `data/`:

```bash
cd punto2/scripts
python3 load_db_data.py
```

### Ingesta programada con cron

```cron
0 * * * * cd /home/ubuntu/project/punto3/scripts && /home/ubuntu/project/.venv/bin/python3 ingest_all.py >> /home/ubuntu/ingest.log 2>&1
```

Esto corre la ingesta cada hora. Cambiar `0 * * * *` por la cadencia deseada
(`0 0 * * *` para diaria a medianoche, etc.).

---

## 2. AWS Glue — capa trusted

Después de que llegan archivos nuevos a `raw/`, se corre el job
**`punto4/scripts/glue_raw_to_trusted.py`**.

### Qué hace el job

- Lee los CSV de `raw/` por dataset.
- Limpia tipos, strings nulos placeholder (`""`, `null`, `N/A`), duplicados.
- Aplica reglas de negocio: `profit_usd`, `roi_pct`, `revenue_cop`
  (USD → COP con la tasa de `exchange`), normalización de géneros, etc.
- Escribe **Parquet + Snappy** en `trusted/` con 6 tablas: `movies`,
  `movie_genres`, `tv_shows`, `people`, `movie_reviews`, `exchange`.

### Configuración del Glue Job

1. Subir `punto4/scripts/glue_raw_to_trusted.py` como script del job.
2. Tipo: **Spark Script Editor**, Glue 5.1 (Spark 3.5 + Python 3).
3. Worker `G.1X`, 10 workers, IAM role `LabRole`.
4. Parámetros del job:

   | Parámetro | Ejemplo |
   |-----------|---------|
   | `--RAW_PREFIX` | `s3://movie-analytics-lake2/raw/` |
   | `--TRUSTED_PREFIX` | `s3://movie-analytics-lake2/trusted/` |

5. Correr después de cada ingesta (manual, cron o EventBridge).

Tiempo típico: ~2 minutos, ~0.54 DPU·h.

---

## 3. Glue Data Catalog

Crear el crawler `trusted-movies-crawler` apuntando a
`s3://movie-analytics-lake2/trusted/` con role `LabRole` y database destino
`movie_trusted_db`. El crawler infiere automáticamente los esquemas Parquet
y crea las 6 tablas, dejándolas listas para Athena y SparkSQL.

---

## 4. Consultas: Athena o PySpark

Ambos motores responden las mismas cinco preguntas de negocio:

1. Géneros con el mayor revenue (USD y COP).
2. Actores que aparecen en películas rentables (`profit_usd > 0`).
3. Revenue en COP por año de estreno, con la tasa de cambio aplicada.
4. Directores con el mejor ROI promedio.
5. Correlación entre ratings y métricas financieras.

### Athena

1. Abrir **Amazon Athena**, database `movie_trusted_db`.
2. Usar las queries del notebook `punto6/queries/sparksql_queries.ipynb`
   (la sintaxis es compatible).
3. Ejecutar **un bloque a la vez** (un `SELECT` por ejecución).
4. La sintaxis Athena usa `CROSS JOIN UNNEST(SPLIT(...))` en vez de
   `LATERAL VIEW explode`.

### PySpark

Notebook `punto6/queries/sparksql_queries.ipynb` (Colab o Glue Notebooks):

1. Configurar credenciales AWS (las temporales del lab requieren
   `aws_session_token`).
2. Cargar el Parquet trusted desde S3.
3. Registrar las vistas: `movies`, `movie_genres`, `people`, `movie_reviews`,
   `exchange`.
4. Ejecutar las queries con `spark.sql(...)`.

---

## 5. PySpark — capa curated

El job **`punto7/scripts/analisis_pyspark.py`** toma la capa trusted y
materializa los resultados de las 5 preguntas en 6 tablas Parquet dentro de
`s3://movie-analytics-lake2/curated/`:

| Tabla `curated/` | Pregunta |
|------------------|----------|
| `revenue_by_genre` | Q1: géneros más rentables |
| `top_actors_rentables` | Q2: actores en películas rentables |
| `revenue_by_year` | Q3: revenue USD/COP por año (desde 1980) |
| `roi_by_director` | Q4: directores con mejor ROI |
| `ratings_correlations` | Q5a: 6 coeficientes globales |
| `ratings_vs_revenue_sample` | Q5b: sample para scatter rating vs revenue |

### Configuración

Parámetros:

| Parámetro | Default |
|-----------|---------|
| `--TRUSTED_PREFIX` | `s3://movie-analytics-lake2/trusted/` |
| `--CURATED_PREFIX` | `s3://movie-analytics-lake2/curated/` |
| `--DECADE_FROM` | `1980` |
| `--MIN_DIR_MOVIES` | `3` |
| `--SAMPLE_SIZE` | `2000` |

Tiempo obtenido: ~1m 37s, ~0.27 DPU·h.

---

## 6. Dashboard Streamlit + API Gateway

La app en `punto8/app/` lee la capa `curated/` con `s3fs + pyarrow` y muestra
4 KPIs globales y 5 secciones (uno por pregunta) con visualizaciones Plotly. Se
despliega en una segunda EC2 (Ubuntu 26.0)

### Desplegar

```bash
scp -i clave.pem -r punto8/app ubuntu@<EC2_IP>:~/app

# En la EC2
cd ~/app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
```

---

## Workflow típico

1. Refrescar archivos en `data/` y recargar MariaDB si hace falta
   (`punto2/scripts/load_db_data.py`).
2. **Ingestar** desde la EC2: `python3 punto3/scripts/ingest_all.py` →
   nuevos objetos bajo `raw/`.
3. **Transformar** en AWS: Glue Job `movie-raw-to-trusted-etl` → Parquet
   bajo `trusted/`.
4. **Catalogar**: correr el crawler `trusted-movies-crawler` (Punto 5).
5. **Validar** las queries en Athena o en
   `punto6/queries/sparksql_queries.ipynb`.
6. **Materializar** la zona curated con el Glue Job
   `movie-trusted-to-curated` (Punto 7).
7. **Refrescar** el dashboard (botón *Recargar datos* en la barra lateral)
   o reiniciar Streamlit.

---

## Dependencias

```bash
pip install -r requirements.txt
```

- **Ingesta:** `boto3`, `pandas`, `pymysql`, `requests`, `sqlalchemy`.
- **Dashboard:** `streamlit`, `pandas`, `plotly`, `pyarrow`, `s3fs`, `boto3`.
- **Glue Jobs:** usan las librerías provistas por el runtime de AWS Glue 5.1.