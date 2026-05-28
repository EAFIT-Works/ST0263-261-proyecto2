"""
CSS personalizado del dashboard (tema azul moderno).

Se inyecta una sola vez en streamlit_app.py mediante
`st.markdown(CUSTOM_CSS, unsafe_allow_html=True)`.
"""

CUSTOM_CSS = """
<style>
/* ── Global ─────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="stApp"] {
    font-family: 'Inter', system-ui, sans-serif !important;
    background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 50%, #eff6ff 100%) !important;
}

/* ── Header ────────────────────────────────────────────────────── */
.stApp .stAppHeader {
    background: transparent !important;
}

.main-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #2563eb 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(37, 99, 235, 0.2);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}

.main-header::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: 10%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
    border-radius: 50%;
}

.main-header h1 {
    color: white !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
    margin-bottom: 0.25rem !important;
    position: relative;
    z-index: 1;
}

.main-header p {
    color: #bfdbfe !important;
    font-size: 0.85rem !important;
    margin: 0 !important;
    position: relative;
    z-index: 1;
}

/* ── Stat cards ────────────────────────────────────────────────── */
.stat-card {
    background: white;
    border: 1px solid #dbeafe;
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 2px 12px rgba(37, 99, 235, 0.06);
    transition: all 0.3s ease;
}

.stat-card:hover {
    box-shadow: 0 8px 30px rgba(37, 99, 235, 0.12);
    transform: translateY(-2px);
}

.stat-accent {
    width: 4px;
    border-radius: 2px;
    flex-shrink: 0;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e3a8a;
    line-height: 1.2;
}

.stat-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Cards genéricas ───────────────────────────────────────────── */
.chart-card {
    background: white;
    border: 1px solid #dbeafe;
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(37, 99, 235, 0.06);
    margin-bottom: 1rem;
}

.chart-card h3 {
    color: #1e3a8a !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    margin-bottom: 0.25rem !important;
}

.chart-card .subtitle {
    color: #64748b !important;
    font-size: 0.85rem !important;
    margin-bottom: 1rem !important;
}

/* ── Sidebar ───────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%) !important;
    border-right: none !important;
}

section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stText {
    color: #bfdbfe !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: white !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}

section[data-testid="stSidebar"] code {
    background: rgba(255,255,255,0.1) !important;
    color: #93c5fd !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
}

/* ── Tabs ──────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: white !important;
    border-radius: 16px !important;
    padding: 6px !important;
    box-shadow: 0 2px 12px rgba(37, 99, 235, 0.06) !important;
    border: 1px solid #dbeafe !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 12px !important;
    padding: 10px 20px !important;
    font-weight: 500 !important;
    color: #64748b !important;
    transition: all 0.3s ease !important;
    font-size: 0.9rem !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: #eff6ff !important;
    color: #1e3a8a !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ── Dataframe ─────────────────────────────────────────────────── */
.stDataFrame {
    border-radius: 16px !important;
    border: 1px solid #dbeafe !important;
    overflow: hidden !important;
}

/* ── Expander ──────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: white !important;
    border: 1px solid #dbeafe !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    transition: all 0.3s ease !important;
}

[data-testid="stExpander"]:hover {
    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.1) !important;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
    color: #1e3a8a !important;
    font-weight: 500 !important;
}

[data-testid="stExpander"] svg {
    color: #1e3a8a !important;
    fill: #1e3a8a !important;
}

/* ── Multiselect ───────────────────────────────────────────────── */
.stMultiSelect label {
    color: #1e3a8a !important;
    font-weight: 500 !important;
}

/* ── Botón recargar ────────────────────────────────────────────── */
.sidebar-btn {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}

.sidebar-btn:hover {
    background: rgba(255,255,255,0.2) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
}

/* ── Scrollbar ─────────────────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #93c5fd;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #60a5fa;
}

/* ── Info box ──────────────────────────────────────────────────── */
.stAlert [data-testid="stAlertInfo"] {
    background: #eff6ff !important;
    border-color: #bfdbfe !important;
    border-radius: 16px !important;
}
</style>
"""
