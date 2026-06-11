import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------------------------
# 1️⃣ Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Frota Inteligente Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
        .main { background-color: #0f172a; }
        [data-testid="stMetric"] {
            background-color: #1e293b;
            padding: 18px 22px;
            border-radius: 14px;
            border: 1px solid #334155;
        }
        [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
        .stButton > button {
            background-color: #10b981;
            color: white;
            border-radius: 10px;
            width: 100%;
            font-weight: 600;
        }
        .stDownloadButton > button {
            background-color: #3b82f6;
            color: white;
            border-radius: 10px;
            width: 100%;
            font-weight: 600;
        }
        [data-testid="stSidebar"] { background-color: #0f172a; }
        .block-container { padding-top: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2️⃣ Constantes & Secrets
# ---------------------------------------------------------------------------
SHEET_URL = st.secrets.get(
    "gsheets_url",
    "https://docs.google.com/spreadsheets/d/1900KpIS6XXANllpWSqqVaUFkUFYXcvcGXW2cf3V6UDY/edit",
)

conn = st.connection("gsheets", type=GSheetsConnection)

# ---------------------------------------------------------------------------
# 3️⃣ Carregamento & limpeza de dados
# ---------------------------------------------------------------------------
def _clean_numeric(series: pd.Series) -> pd.Series:
    """Remove símbolos de moeda e converte para float."""
    if series.dtype == object:
        series = (
            series.astype(str)
            .str.replace(r"[R$\s]", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
    return pd.to_numeric(series, errors="coerce")


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = [
        "Valor Total", "Litros", "Preço por Litro",
        "Quilometragem", "KM Atual", "KM Anterior",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = _clean_numeric(df[col])

    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce").dt.normalize()

    return df


@st.cache_data(ttl=300)
def load_sheet_data() -> pd.DataFrame:
    try:
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        return _clean_dataframe(df)
    except Exception as exc:
        st.error(f"⚠️ Falha ao conectar à planilha: {exc}")
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# 4️⃣ Sidebar – Navegação & autenticação
# ---------------------------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3408/3408506.png", width=90)
st.sidebar.title("Frota Inteligente")
perfil = st.sidebar.selectbox("Módulo de Acesso", ["Motorista", "Gestor Administrativo"])

if "auth" not in st.session_state:
    st.session_state.auth = False

if perfil == "Gestor Administrativo":
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    if senha and senha == "admin123":
        st.session_state.auth = True
        st.sidebar.success("✅ Acesso Autorizado")
    elif senha:
        st.session_state.auth = False
        st.sidebar.error("❌ Senha incorreta")

# ---------------------------------------------------------------------------
# 5️⃣ Módulo Motorista
# ---------------------------------------------------------------------------
if perfil == "Motorista":
    st.title("⛽ Registro de Atividade")
    st.markdown("Clique no botão abaixo para registrar um novo abastecimento.")
    formulario_url = st.secrets.get("form_url", "https://forms.gle/e3tVoSTAFGGU3T787")
    st.link_button("ABRIR FORMULÁRIO DE ABASTECIMENTO", formulario_url)
    st.info("🛈 Após enviar o formulário, os dados serão processados pela central.")

# ---------------------------------------------------------------------------
# 6️⃣ Módulo Gestor
# ---------------------------------------------------------------------------
else:
    st.title("📊 Painel de Controle Estratégico")

    if not st.session_state.auth:
        st.warning("🔐 Insira a senha para visualizar o painel.")
        st.stop()

    df = load_sheet_data()

    if df.empty:
        st.warning("⚠️ Planilha vazia ou não carregada.")
        st.stop()

    # ── Botão para forçar atualização dos dados ──────────────────────────
    if st.sidebar.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

    # ── Filtros na sidebar ───────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Filtros")

    # Veículo
    veiculos = ["Todos"] + sorted(df["Veículo"].dropna().unique().tolist()) if "Veículo" in df.columns else ["Todos"]
    filtro_veiculo = st.sidebar.selectbox("🚗 Veículo", veiculos)

    # Placa
    placas = ["Todos"] + sorted(df["Placa"].dropna().unique().tolist()) if "Placa" in df.columns else ["Todos"]
    filtro_placa = st.sidebar.selectbox("🔢 Placa", placas)

    # Combustível
    combust = ["Todos"] + sorted(df["Tipo Combustível"].dropna().unique().tolist()) if "Tipo Combustível" in df.columns else ["Todos"]
    filtro_combust = st.sidebar.selectbox("⛽ Combustível", combust)

    # Período
    if "Data" in df.columns:
        datas_validas = df["Data"].dropna()
        if not datas_validas.empty:
            data_min = datas_validas.min().date()
            data_max = datas_validas.max().date()
            filtro_periodo = st.sidebar.date_input(
                "📅 Período",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max,
            )
        else:
                total_gasto = pd.to_numeric(df["Valor Total"], errors="coerce").sum()
                col1, col2 = st.columns(2)
                col1.metric("Gasto Total", f"R$ {total_gasto:,.2f}")
                if "Data" in df.columns:
                    col2.metric("Abastecimentos", df.shape[0])
            else:
                st.error("❌ Coluna 'Valor Total' não encontrada. Verifique o nome exato na planilha.")

            # -------------------------------------------------------------------
            # Visualizações – gráfico de gastos mensais
            # -------------------------------------------------------------------
            if "Data" in df.columns and "Valor Total" in df.columns:
                # Data já convertida por _clean_dataframe(); força novamente se necessário
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
                df["Valor Total"] = pd.to_numeric(df["Valor Total"], errors="coerce")
                df_valid = df.dropna(subset=["Data", "Valor Total"]).copy()
                if not df_valid.empty:
                    df_valid["Mês"] = df_valid["Data"].dt.to_period("M").astype(str)
                    mensal = (
                        df_valid.groupby("Mês")["Valor Total"]
                        .sum()
                        .reset_index()
                    )
                    fig = px.bar(
                        mensal,
                        x="Mês",
                        y="Valor Total",
                        title="Gastos Mensais",
                        color="Valor Total",
                        color_continuous_scale="Teal",
                        template="plotly_dark",
                    )
                    fig.update_layout(
                        yaxis_tickprefix="R$ ",
                        yaxis_tickformat=",.2f",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📅 Nenhuma data válida encontrada para o gráfico de gastos mensais.")
            else:
                st.info("🔎 Adicione colunas 'Data' e 'Valor Total' para gráficos adicionais.")
