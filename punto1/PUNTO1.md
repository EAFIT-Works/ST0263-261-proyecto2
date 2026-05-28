# Caso de estudio y preguntas de negocio

## 1.1 Caso de estudio

**Análisis financiero de películas usando múltiples fuentes de datos.**

La industria del entretenimiento maneja un catálogo masivo de películas con
métricas financieras (presupuesto, ingresos, ganancia, ROI) que se reportan
casi siempre en dólares estadounidenses, mientras los inversionistas y el
público latinoamericanos suelen razonar en pesos colombianos. Este proyecto combina:

1. **Catálogo de títulos** (películas y series) almacenado en archivos dentro de una EC2.
2. **Datos transaccionales** de personas y reseñas en una base relacional MariaDB sobre RDS.
3. **Datos en línea** consumidos desde la API pública de tasas de cambio, que permite convertir las métricas financieras a la moneda local.

Con esto respondemos preguntas sobre rentabilidad histórica de películas
considerando revenue, ROI y tasas de cambio.

## 1.2 Distribución entre las 3 fuentes (Punto 2)

| Fuente | Tipo | Contenido |
|--------|------|-----------|
| **EC2 — servidor de archivos** | Archivos en `/home/ubuntu/project/data/` | `movies.csv`, `tv_shows.csv` |
| **RDS MariaDB** (BD `movies`) | Base de datos relacional | Tablas `people` y `movie_reviews` |
| **URL pública** | HTTPS / REST | Tasas de cambio diarias desde [exchangerate-api.com](https://www.exchangerate-api.com/) |

## 1.3 Preguntas de negocio

### Pregunta 1 — Géneros más rentables

¿Qué **géneros** generan el mayor **revenue total**?

### Pregunta 2 — Actores en películas rentables

¿Qué **actores** aparecen con mayor frecuencia en películas **rentables**?

### Pregunta 3 — Revenue ajustado a COP en el tiempo

¿Cómo evoluciona el **revenue** (en USD y en COP) a lo largo de los **años**?

### Pregunta 4 — Directores con mejor ROI

¿Qué **directores** tienen el mejor **ROI promedio**?

### Pregunta 5 — Correlación entre rating y ganancias

¿Existe **correlación** entre los **ratings** y las **métricas financieras**
(revenue, profit, ROI)?

## 1.4 Esquema del dataset

| Tabla | Filas | Columnas clave |
|-------|------:|----------------|
| `movies` | 22,393 | `tmdb_id`, `title`, `release_year`, `revenue_usd`, **`revenue_cop`**, `profit_usd`, `roi_pct`, `budget_usd`, `vote_average`, `cast_ids`, `directors`, `genres` |
| `movie_genres` | 50,156 | `tmdb_id`, `genre` (relación N:M película-género) |
| `people` | 58,393 | `tmdb_id`, `name`, `known_for_dept` |
| `movie_reviews` | 22,712 | `tmdb_id`, `review_id`, `author`, `rating`, `content` |
| `exchange` | (varias) | `currency`, `rate`, `base`, `date` — tasas vs USD |
| `tv_shows` | (catálogo) | `tmdb_id`, `title`, `original_title`, ... |

## 1.5 Infraestructura usada

Los detalles operativos están en los Puntos 2 y 3.

- **Bucket S3:** `movie-analytics-lake2` con zonas `raw/`, `trusted/`,
  `curated/`.
- **RDS MariaDB:** instancia con BD `movies`, tablas `people` y
  `movie_reviews`.
- **EC2:** instancia Ubuntu Server
  `/home/ubuntu/project/data/` que contiene `movies.csv` y `tv_shows.csv`.
- **API:** `https://api.exchangerate-api.com/v4/latest/USD` (free tier).
- **Glue Data Catalog:** database `movie_trusted_db` con las 6 tablas de
  la zona `trusted/`.