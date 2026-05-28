"""
Tab Correlaciones (Q5): ¿hay relación entre ratings y ganancias?

Combina:
  - 6 cards con las correlaciones de Pearson (tabla `ratings_correlations`).
  - Un scatter rating vs revenue (tabla `ratings_vs_revenue_sample`).
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components import base_layout, section_header
from config import ACCENT, TEAL_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY
from data import load_curated


def _corr_card(label: str, value: float, color: str) -> str:
    """Mini card para mostrar una correlación."""
    if value is None or (isinstance(value, float) and value != value):
        formatted = "n/d"
        sign_color = TEXT_SECONDARY
    else:
        formatted = f"{value:+.3f}"
        sign_color = "#16a34a" if value >= 0 else "#dc2626"

    return f"""
    <div class="stat-card">
        <div style="display:flex; align-items:stretch; gap:14px;">
            <div class="stat-accent" style="background:{color};"></div>
            <div>
                <div class="stat-value" style="color:{sign_color};">{formatted}</div>
                <div class="stat-label">{label}</div>
            </div>
        </div>
    </div>
    """


def render() -> None:
    section_header(
        "Correlación entre ratings y métricas financieras",
        "Coeficientes de Pearson entre ratings (TMDB y reseñas) y revenue/profit/ROI, más un scatter ilustrativo de rating vs revenue.",
    )

    corr_df = load_curated("ratings_correlations")
    if corr_df.empty:
        st.warning("La tabla `ratings_correlations` está vacía.")
        return
    corr = corr_df.iloc[0]

    st.markdown("**Rating TMDB (`vote_average`) vs:**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(_corr_card("Revenue (USD)", corr["corr_tmdb_revenue"], ACCENT), unsafe_allow_html=True)
    with c2:
        st.markdown(_corr_card("Profit (USD)", corr["corr_tmdb_profit"], "#1e40af"), unsafe_allow_html=True)
    with c3:
        st.markdown(_corr_card("ROI (%)", corr["corr_tmdb_roi"], "#1d4ed8"), unsafe_allow_html=True)

    st.markdown("")
    st.markdown("**Rating de reseñas (`movie_reviews.rating` promedio) vs:**")
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(_corr_card("Revenue (USD)", corr["corr_reviews_revenue"], TEAL_ACCENT), unsafe_allow_html=True)
    with c5:
        st.markdown(_corr_card("Profit (USD)", corr["corr_reviews_profit"], "#0f766e"), unsafe_allow_html=True)
    with c6:
        st.markdown(_corr_card("ROI (%)", corr["corr_reviews_roi"], "#134e4a"), unsafe_allow_html=True)

    st.markdown("")
    section_header(
        "Rating TMDB vs Revenue (sample)",
        f"Muestra aleatoria de hasta 2,000 películas. Cada punto es una película.",
    )

    sample = load_curated("ratings_vs_revenue_sample")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sample["vote_average"],
        y=sample["revenue_usd"] / 1e6,
        mode="markers",
        marker=dict(
            size=6,
            color=sample["revenue_usd"],
            colorscale=[[0, "#93c5fd"], [0.5, "#3b82f6"], [1, "#1e3a8a"]],
            opacity=0.6,
            line=dict(width=0),
        ),
        text=sample["title"],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Rating TMDB: %{x:.1f}<br>"
            "Revenue: $%{y:,.1f}M USD<extra></extra>"
        ),
    ))
    fig.update_layout(
        base_layout(height=500),
        xaxis=dict(title=dict(text="Rating TMDB (vote_average)")),
        yaxis=dict(
            title=dict(text="Revenue (Millones USD)"),
            type="log",
        ),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    with st.expander("Interpretación de las correlaciones"):
        st.markdown(
            "- Un valor cercano a **+1** indica que más rating se asocia con más ganancia.\n"
            "- Un valor cercano a **0** indica poca o ninguna relación lineal.\n"
            "- Valores **negativos** indican relación inversa (mayor rating con menor ganancia).\n"
            "\n"
            "Las correlaciones bajas son comunes en este dominio: el rating es un factor de "
            "percepción y no captura presupuesto de marketing, estacionalidad ni saga, que son "
            "drivers fuertes del revenue."
        )
