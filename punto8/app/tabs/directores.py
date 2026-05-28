"""
Tab Directores (Q4): top 20 directores con mejor ROI promedio.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components import base_layout, section_header
from config import TEXT_PRIMARY
from data import load_curated


def render() -> None:
    section_header(
        "Directores con mejor ROI promedio",
        "Top 20 directores ordenados por ROI promedio (%), considerando solo aquellos con al menos 3 películas con revenue conocido.",
    )

    df_full = load_curated("roi_by_director")
    df = df_full.sort_values("avg_roi_pct", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["director_name"],
        x=df["avg_roi_pct"],
        orientation="h",
        marker=dict(
            color=df["avg_roi_pct"],
            colorscale=[[0, "#93c5fd"], [0.5, "#3b82f6"], [1, "#1e3a8a"]],
            line=dict(width=0),
            cornerradius=6,
        ),
        text=[f"{v:,.0f}%" for v in df["avg_roi_pct"]],
        textposition="outside",
        textfont=dict(size=10, color=TEXT_PRIMARY, family="Inter"),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "ROI promedio: %{x:,.1f}%<br>"
            "Películas: %{customdata[0]}<br>"
            "Profit promedio: $%{customdata[1]:,.0f}<extra></extra>"
        ),
        customdata=df[["n_movies", "avg_profit_usd"]].values,
        width=0.6,
    ))
    fig.update_layout(
        base_layout(height=580),
        xaxis=dict(
            title=dict(text="ROI promedio (%)"),
            range=[0, df["avg_roi_pct"].max() * 1.15],
        ),
        yaxis=dict(tickfont=dict(size=11, color=TEXT_PRIMARY, family="Inter")),
    )
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    with st.expander("Ver tabla detallada"):
        display = df_full.sort_values("avg_roi_pct", ascending=False).rename(
            columns={
                "director_name": "Director",
                "n_movies": "# películas",
                "avg_roi_pct": "ROI promedio (%)",
                "avg_profit_usd": "Profit promedio (USD)",
                "total_revenue_usd": "Revenue total (USD)",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)
