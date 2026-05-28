"""
Tab Histórico (Q3): evolución del revenue (USD y COP) por año desde 1980.
"""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from components import base_layout, section_header
from config import ACCENT, TEAL_ACCENT
from data import load_curated


def render() -> None:
    section_header(
        "Evolución del revenue por año (desde 1980)",
        "Revenue total acumulado por año en USD y en COP. La conversión usa la columna revenue_cop pre-calculada en la zona trusted/.",
    )

    df = load_curated("revenue_by_year").sort_values("release_year")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df["release_year"],
            y=df["revenue_usd_total"] / 1e9,
            name="Revenue USD (B)",
            mode="lines+markers",
            line=dict(color=ACCENT, width=3, shape="spline"),
            marker=dict(size=6, color=ACCENT, line=dict(width=2, color="white")),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.08)",
            hovertemplate="<b>Año %{x}</b><br>Revenue USD: $%{y:.2f}B<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["release_year"],
            y=df["revenue_cop_total"] / 1e12,
            name="Revenue COP (T)",
            mode="lines+markers",
            line=dict(color=TEAL_ACCENT, width=3, shape="spline", dash="dot"),
            marker=dict(size=6, color=TEAL_ACCENT, line=dict(width=2, color="white")),
            hovertemplate="<b>Año %{x}</b><br>Revenue COP: $%{y:.2f}T<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(base_layout(height=480))
    fig.update_xaxes(title=dict(text="Año de estreno"))
    fig.update_yaxes(title=dict(text="Revenue (Billones USD)"), secondary_y=False)
    fig.update_yaxes(title=dict(text="Revenue (Trillones COP)"), secondary_y=True)
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    with st.expander("Ver tabla con # películas y ROI promedio por año"):
        display = df.rename(
            columns={
                "release_year": "Año",
                "n_movies": "# películas",
                "revenue_usd_total": "Revenue (USD)",
                "revenue_cop_total": "Revenue (COP)",
                "avg_roi_pct": "ROI promedio (%)",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)
