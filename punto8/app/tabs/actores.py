"""
Tab Actores (Q2): top 25 actores con más películas rentables.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components import base_layout, section_header
from config import TEXT_PRIMARY
from data import load_curated


def render() -> None:
    section_header(
        "Actores en más películas rentables",
        "Top 25 actores ordenados por número de películas con profit positivo. La tabla incluye también la ganancia y revenue promedio.",
    )

    df_full = load_curated("top_actors_rentables")
    df = df_full.sort_values("n_movies_rentables", ascending=True)

    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df["actor_name"],
            x=df["n_movies_rentables"],
            orientation="h",
            marker=dict(
                color=df["n_movies_rentables"],
                colorscale=[[0, "#5eead4"], [0.5, "#0d9488"], [1, "#0f766e"]],
                line=dict(width=0),
                cornerradius=6,
            ),
            text=df["n_movies_rentables"].astype(str),
            textposition="outside",
            textfont=dict(size=10, color=TEXT_PRIMARY, family="Inter"),
            hovertemplate="<b>%{y}</b><br>Películas rentables: %{x}<extra></extra>",
            width=0.6,
        ))
        fig.update_layout(
            base_layout(height=640),
            xaxis=dict(
                title=dict(text="# películas rentables"),
                range=[0, df["n_movies_rentables"].max() * 1.12],
            ),
            yaxis=dict(tickfont=dict(size=10, color=TEXT_PRIMARY, family="Inter")),
        )
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    with col_table:
        display = df_full.sort_values("n_movies_rentables", ascending=False)[
            ["actor_name", "n_movies_rentables", "avg_profit_usd"]
        ].rename(
            columns={
                "actor_name": "Actor",
                "n_movies_rentables": "# películas",
                "avg_profit_usd": "Profit promedio (USD)",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander("Ver tabla detallada"):
        full = df_full.sort_values("n_movies_rentables", ascending=False).rename(
            columns={
                "actor_id": "ID",
                "actor_name": "Actor",
                "n_movies_rentables": "# películas rentables",
                "avg_profit_usd": "Profit promedio (USD)",
                "total_revenue_usd": "Revenue total (USD)",
            }
        )
        st.dataframe(full, use_container_width=True, hide_index=True)
