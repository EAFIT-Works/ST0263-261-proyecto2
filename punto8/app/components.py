"""
Componentes reutilizables: plantilla base de Plotly y tarjetas HTML.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from config import GRID_COLOR, TEXT_PRIMARY, TEXT_SECONDARY


def base_layout(title: str = "", height: int = 450) -> dict:
    """Layout de Plotly compartido por todas las gráficas del dashboard."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=50, r=30, t=40, b=50),
        title=dict(text=title, font=dict(size=14, color=TEXT_PRIMARY, family="Inter"), x=0),
        xaxis=dict(
            gridcolor=GRID_COLOR, gridwidth=1, zeroline=False,
            tickfont=dict(size=11, color=TEXT_SECONDARY),
            title=dict(font=dict(size=12, color=TEXT_PRIMARY)),
            linecolor=GRID_COLOR,
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR, gridwidth=1, zeroline=False,
            tickfont=dict(size=11, color=TEXT_SECONDARY),
            title=dict(font=dict(size=12, color=TEXT_PRIMARY)),
            linecolor=GRID_COLOR,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=TEXT_SECONDARY),
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#dbeafe",
            font=dict(size=12, family="Inter", color=TEXT_PRIMARY),
        ),
    )


def stat_card(label: str, value: str, color: str) -> str:
    """Tarjeta de estadística usada en la fila superior del dashboard.

    El `color` se usa como acento vertical lateral para diferenciar cada
    tarjeta sin necesidad de iconos.
    """
    return f"""
    <div class="stat-card">
        <div style="display:flex; align-items:stretch; gap:14px;">
            <div class="stat-accent" style="background:{color};"></div>
            <div>
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
        </div>
    </div>
    """


def section_header(title: str, subtitle: str) -> None:
    """Encabezado pequeño con título + subtítulo dentro de cada tab."""
    st.markdown(
        f"""
        <div style="margin-bottom:1rem;">
            <h3 style="color:{TEXT_PRIMARY}; font-weight:600; font-size:1.1rem; margin:0;">{title}</h3>
            <p style="color:{TEXT_SECONDARY}; font-size:0.85rem; margin:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart(fig: go.Figure, height: int = 440) -> None:
    """Aplica el layout base y dibuja la figura sin la barra de Plotly."""
    fig.update_layout(base_layout(height=height))
    st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
