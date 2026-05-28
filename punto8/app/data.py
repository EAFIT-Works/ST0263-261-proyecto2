"""
Acceso a la zona curated/ del Data Lake con caché de Streamlit.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import CURATED


@st.cache_data(ttl=3600, show_spinner="Cargando datos desde el Data Lake...")
def load_curated(name: str) -> pd.DataFrame:
    """Lee una tabla Parquet de la zona curated/ (cache 1 hora)."""
    return pd.read_parquet(f"{CURATED}/{name}/")
