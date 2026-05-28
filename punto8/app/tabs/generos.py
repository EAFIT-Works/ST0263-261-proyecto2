"""
Tab Géneros (Q1): géneros con mayor revenue total.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components import base_layout, section_header
from config import TEXT_PRIMARY
from data import load_curated


def render() -> None:
    section_header(
        "Géneros con mayor revenue total",
        "Top 15 géneros ordenados por revenue acumulado en USD. La conversión a COP se muestra en la tabla detallada.",
    )

    df = (
        load_curated("revenue_by_genre")
        .sort_values("revenue_usd_total", ascending=False)
        .head(15)
        .sort_values("revenue_usd_total", ascending=True)
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["genre"],
        x=df["revenue_usd_total"] / 1e9,
        orientation="h",
        marker=dict(
            color=df["revenue_usd_total"],
            colorscale=[[0, "#93c5fd"], [0.5, "#3b82f6"], [1, "#1e3a8a"]],
            line=dict(width=0),
            cornerradius=8,
        ),
        text=[f"${v/1e9:.1f}B" for v in df["revenue_usd_total"]],
        textposition="outside",
        textfont=dict(size=11, color=TEXT_PRIMARY, family="Inter"),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:.2f}B USD<extra></extra>",
        width=0.65,
    ))
    fig.update_layout(
        base_layout(height=520),
        xaxis=dict(
            title=dict(text="Revenue total (Billones USD)"),
            range=[0, df["revenue_usd_total"].max() / 1e9 * 1.15],
        ),
        yaxis=dict(tickfont=dict(size=12, color=TEXT_PRIMARY, family="Inter")),
    )
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    with st.expander("Ver tabla detallada (USD y COP)"):
        display = df.sort_values("revenue_usd_total", ascending=False).rename(
            columns={
                "genre": "Género",
                "n_movies": "# películas",
                "revenue_usd_total": "Revenue total (USD)",
                "revenue_usd_avg": "Revenue promedio (USD)",
                "revenue_cop_total": "Revenue total (COP)",
                "revenue_cop_avg": "Revenue promedio (COP)",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)
