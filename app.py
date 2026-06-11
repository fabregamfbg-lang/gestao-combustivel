import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# -------------------------------------------------------
# Configuração da página
# -------------------------------------------------------
st.set_page_config(
    page_title="Frota Inteligente Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
        .main {background-color: #0f172a;}
        .stMetric {background-color: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155;}
        .stButton>button {background-color: #10b981; color: white; border-radius: 10px; width: 100%;}
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Conexão com Google Sheets
# -------------------------------------------------------
SHEET_URL = st.secrets.get(
    "gsheets_url",
    "https://docs.google.com/spreadsheets/d/1900KpIS6XXANllpWSqqVaUFkUFYXcvcGXW2cf3V6UDY/edit",
)

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_sheet_data():
    try:
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        return df if df is not None else pd.DataFrame()
    except Exception as exc:
        st.error(f"Falha ao conectar: {exc}")
        return pd.DataFrame()

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3408/3408506.png", width=100)
st.sidebar.title("Frota Inteligente")
perfil = st.sidebar.selectbox("Módulo de Acesso", ["Motorista", "Gestor Administrativo"])

if "auth" not in st.session_state:
    st.session_state.auth = False

if perfil == "Gestor Administrativo":
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    if senha == "admin123":
        st.session_state.auth = True
        st.sidebar.success("Acesso Autorizado")
    elif senha:
        st.sidebar.error("Senha incorreta")

# -------------------------------------------------------
# Módulo Motorista
# -------------------------------------------------------
if perfil == "Motorista":
    st.title("Registro de Atividade")
    formulario_url = st.secrets.get("form_url", "https://forms.gle/e3tVoSTAFGGU3T787")
    st.link_button("ABRIR FORMULÁRIO DE ABASTECIMENTO", formulario_url)
    st.info("Após enviar o formulário, os dados serão processados pela central.")

# -------------------------------------------------------
# Módulo Gestor
# -------------------------------------------------------
else:
    st.title("Painel de Controle Estratégico")
    if not st.session_state.auth:
        st.warning("Insira a senha para visualizar o painel.")
    else:
        df = load_sheet_data()
        if df.empty:
            st.warning("Planilha vazia ou não carregada.")
        else:
            st.success(f"Dados carregados – {len(df)} linhas.")
            st.dataframe(df, use_container_width=True)

            if "Valor Total" in df.columns:
                col1, col2 = st.columns(2)
                col1.metric("Gasto Total", f"R$ {df['Valor Total'].sum():,.2f}")
                if "Data" in df.columns:
                    col2.metric("Abastecimentos", df.shape[0])
            else:
                st.error("Coluna 'Valor Total' não encontrada na planilha.")

            if "Data" in df.columns and "Valor Total" in df.columns:
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
                df_valid = df.dropna(subset=["Data"])
                if not df_valid.empty:
                    df_valid = df_valid.copy()
                    df_valid["Mes"] = df_valid["Data"].dt.to_period("M").astype(str)
                    mensal = df_valid.groupby("Mes")["Valor Total"].sum().reset_index()
                    fig = px.bar(mensal, x="Mes", y="Valor Total",
                                 title="Gastos Mensais", color="Valor Total",
                                 template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
