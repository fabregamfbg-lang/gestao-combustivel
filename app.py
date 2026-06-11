Revised Streamlit app with improved structure, caching, security, and UI enhancements

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------------------------
# 1️⃣ Page configuration (modern dark corporate theme)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Frota Inteligente Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a premium look (glassmorphism, rounded cards)
st.markdown(
    """
    <style>
        .main {background-color: #0f172a;}
        .stMetric {background-color: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155;}
        .stButton>button {background-color: #10b981; color: white; border-radius: 10px; width: 100%;}
        .stTextInput>div>div>input {background-color: #1e293b; color: white; border-radius: 10px;}
        .css-1cpxqw2 {background: rgba(255,255,255,0.05); backdrop-filter: blur(8px); border-radius: 12px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 2️⃣ Centralised constants & Secrets
# ---------------------------------------------------------------------------
# Store the Google Sheet URL in Streamlit secrets (recommended for production)
# In local testing you can still fall back to a hard‑coded placeholder.
SHEET_URL = st.secrets.get("gsheets_url", "https://docs.google.com/spreadsheets/d/1900KpIS6XXANllpWSqqVaUFkUFYXcvcGXW2cf3V6UDY/edit")

# Initialise the connection once (must be before any function that uses it)
conn = st.connection("gsheets", type=GSheetsConnection)

# ---------------------------------------------------------------------------
# 3️⃣ Data loading utilities (cached for performance)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)  # cache for 5 minutes – refresh automatically
def load_sheet_data() -> pd.DataFrame:
    """Read the Google Sheet into a pandas DataFrame.
    Returns an empty DataFrame on failure so the rest of the UI can handle it gracefully.
    """
    try:
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception as exc:
        st.error(f"⚠️ Falha ao conectar à planilha: {exc}")
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# 4️⃣ Sidebar – navigation & authentication
# ---------------------------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3408/3408506.png", width=100)
st.sidebar.title("Frota Inteligente")
perfil = st.sidebar.selectbox("Módulo de Acesso", ["Motorista", "Gestor Administrativo"])

# Simple password handling – stored in session state to avoid re‑prompting
if "auth" not in st.session_state:
    st.session_state.auth = False

if perfil == "Gestor Administrativo":
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    if senha and senha == "admin123":
        st.session_state.auth = True
        st.sidebar.success("✅ Acesso Autorizado")
    elif senha:
        st.sidebar.error("❌ Senha incorreta")

# ---------------------------------------------------------------------------
# 5️⃣ Main application logic
# ---------------------------------------------------------------------------
if perfil == "Motorista":
    st.title("⛽ Registro de Atividade")
    st.markdown("Clique no botão abaixo para registrar um novo abastecimento.")
    # Link to Google Form – keep URL in secrets for easy change
    formulario_url = st.secrets.get("form_url", "https://forms.gle/e3tVoSTAFGGU3T787")
    st.link_button("ABRIR FORMULÁRIO DE ABASTECIMENTO", formulario_url)
    st.info("🛈 Após enviar o formulário, os dados serão processados pela central.")
else:
    st.title("📊 Painel de Controle Estratégico")
    if not st.session_state.auth:
        st.warning("🔐 Insira a senha para visualizar o painel.")
    else:
        df = load_sheet_data()
        if df.empty:
            st.warning("⚠️ Planilha vazia ou não carregada. Verifique o conteúdo.")
        else:
            st.success(f"📥 Dados carregados – {len(df)} linhas.")
            st.dataframe(df, use_container_width=True)

            # -------------------------------------------------------------------
            # 5️⃣1️⃣ Métricas principais (ex.: Gasto Total)
            # -------------------------------------------------------------------
            if "Valor Total" in df.columns:
                total_gasto = df["Valor Total"].sum()
                col1, col2 = st.columns(2)
                col1.metric("Gasto Total", f"R$ {total_gasto:,.2f}")
                # Exemplo de métrica adicional – número de abastecimentos
                if "Data" in df.columns:
                    col2.metric("Abastecimentos", f"{df.shape[0]}")
            else:
                st.error("❌ Coluna 'Valor Total' não encontrada. Verifique o nome na planilha.")

            # -------------------------------------------------------------------
            # 5️⃣2️⃣ Visualizações (gráficos) – opcionais e dependentes das colunas
            # -------------------------------------------------------------------
            if "Data" in df.columns and "Valor Total" in df.columns:
                # Convert date column to datetime (tolerant parsing)
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
                df_valid = df.dropna(subset=["Data"])
                if not df_valid.empty:
                    # Agrupar por mês para visualização de gastos mensais
                    df_valid["Mês"] = df_valid["Data"].dt.to_period("M").astype(str)
                    mensal = df_valid.groupby("Mês")["Valor Total"].sum().reset_index()
                    fig = px.bar(mensal, x="Mês", y="Valor Total", title="Gastos Mensais", color="Valor Total", template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📅 Nenhuma data válida encontrada para o gráfico de gastos mensais.")
            else:
                st.info("🔎 Adicione colunas 'Data' e 'Valor Total' para gráficos adicionais.")
