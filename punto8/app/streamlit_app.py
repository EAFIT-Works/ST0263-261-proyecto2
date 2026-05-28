"""
streamlit_app.py
----------------
Punto de entrada del dashboard "Análisis financiero de películas".

Lee la zona curated/ del Data Lake (productos del Punto 7) y la presenta
con KPIs globales y 5 visualizaciones, una por pregunta de negocio.

Estructura:
    config.py        constantes (bucket, paths, colores)
    styles.py        CSS personalizado
    data.py          load_curated() con caché
    components.py    base_layout, stat_card, section_header
    tabs/            un módulo render() por pregunta
"""

from __future__ import annotations

import streamlit as st

from components import stat_card
from config import ACCENT, BUCKET, CURATED_PREFIX, TEAL_ACCENT
from data import load_curated
from styles import CUSTOM_CSS
from tabs import actores, correlaciones, directores, generos, historico


# =============================================================================
#  Page setup
# =============================================================================

st.set_page_config(
    page_title="Análisis financiero de películas",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
#  Helpers de KPIs
# =============================================================================

def _format_money(value: float, suffix: str, divisor: float) -> str:
    """Formatea un valor monetario grande: 1.23B, 4.56T, etc."""
    if value is None:
        return "n/d"
    return f"${value / divisor:,.2f}{suffix}"


@st.cache_data(ttl=3600, show_spinner=False)
def _global_kpis() -> dict:
    """Agrega KPIs globales desde la tabla revenue_by_year (1 sola lectura)."""
    df = load_curated("revenue_by_year")
    total_movies = int(df["n_movies"].sum())
    total_usd = float(df["revenue_usd_total"].sum())
    total_cop = float(df["revenue_cop_total"].sum())
    weighted_roi = float(
        (df["avg_roi_pct"] * df["n_movies"]).sum() / df["n_movies"].sum()
    )
    return {
        "n_movies": total_movies,
        "revenue_usd": total_usd,
        "revenue_cop": total_cop,
        "roi_pct": weighted_roi,
    }


# =============================================================================
#  Header + KPIs
# =============================================================================

st.markdown(
    '<div class="main-header"><h1>Análisis financiero de películas</h1></div>',
    unsafe_allow_html=True,
)

kpis = _global_kpis()

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        stat_card("Películas analizadas", f"{kpis['n_movies']:,}", "#1e40af"),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        stat_card("Revenue total (USD)", _format_money(kpis["revenue_usd"], "B", 1e9), ACCENT),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        stat_card("Revenue total (COP)", _format_money(kpis["revenue_cop"], "T", 1e12), TEAL_ACCENT),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        stat_card("ROI promedio", f"{kpis['roi_pct']:,.1f}%", "#0f766e"),
        unsafe_allow_html=True,
    )


# =============================================================================
#  Sidebar
# =============================================================================

with st.sidebar:
    st.markdown("### Dashboard")
    st.markdown(
        "Análisis de rentabilidad histórica de películas considerando "
        "revenue, ROI y tasas de cambio USD→COP. Lee la zona `curated/` "
        "que produjo el análisis PySpark del Punto 7."
    )
    st.markdown("---")
    st.markdown(f"**Bucket:** `{BUCKET}`")
    st.markdown(f"**Zona:** `{CURATED_PREFIX}/`")
    st.markdown("---")
    if st.button("Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# =============================================================================
#  Tabs (uno por pregunta de negocio)
# =============================================================================

tab_generos, tab_actores, tab_historico, tab_directores, tab_corr = st.tabs(
    ["Géneros", "Actores", "Histórico", "Directores", "Correlaciones"]
)

with tab_generos:
    generos.render()
with tab_actores:
    actores.render()
with tab_historico:
    historico.render()
with tab_directores:
    directores.render()
with tab_corr:
    correlaciones.render()
