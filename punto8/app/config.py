"""
Configuración compartida del dashboard: ubicación del Data Lake y paleta
de colores.

Variables de entorno:
    S3_BUCKET       bucket del Data Lake.        default: movie-analytics-lake2
    CURATED_PREFIX  prefijo de la zona curated.  default: curated
"""

from __future__ import annotations

import os

# --- Data Lake ---------------------------------------------------------------

BUCKET = os.getenv("S3_BUCKET", "movie-analytics-lake2")
CURATED_PREFIX = os.getenv("CURATED_PREFIX", "curated")
CURATED = f"s3://{BUCKET}/{CURATED_PREFIX}"

# --- Paleta de colores -------------------------------------------------------

BLUES = [
    "#172554", "#1e3a8a", "#1e40af", "#1d4ed8",
    "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd",
]
TEALS = [
    "#134e4a", "#0f766e", "#0d9488", "#14b8a6",
    "#2dd4bf", "#5eead4", "#99f6e4",
]
ACCENT = "#2563eb"
ACCENT_LIGHT = "#3b82f6"
TEAL_ACCENT = "#0d9488"
BG_DARK = "#0f172a"
BG_CARD = "#ffffff"
TEXT_PRIMARY = "#1e3a8a"
TEXT_SECONDARY = "#64748b"
GRID_COLOR = "#e2e8f0"
