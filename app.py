import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
# ---------------------------------------------------------------------------
# 1. Configuração da página
# ---------------------------------------------------------------------------
# -- Pagina ------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Combustível",
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
<style>
.main{background-color:#0f172a}
section[data-testid="stSidebar"]{background-color:#0f172a}
div[data-testid="stMetric"]{background-color:#1e293b;padding:18px 22px;border-radius:14px;border:1px solid #334155}
.stButton>button{background-color:#10b981;color:white;border-radius:10px;width:100%;font-weight:600}
.stDownloadButton>button{background-color:#3b82f6;color:white;border-radius:10px;width:100%;font-weight:600}
.block-container{padding-top:1.5rem}
</style>
""", unsafe_allow_html=True)
# ---------------------------------------------------------------------------
# 2. Constantes & Secrets
# ---------------------------------------------------------------------------
# -- Conexao ----------------------------------------------------------------
SHEET_URL = st.secrets.get(
    "gsheets_url",
    "https://docs.google.com/spreadsheets/d/1900KpIS6XXANllpWSqqVaUFkUFYXcvcGXW2cf3V6UDY/edit",
)
conn = st.connection("gsheets", type=GSheetsConnection)
# ---------------------------------------------------------------------------
# 3. Carregamento & limpeza de dados
# ---------------------------------------------------------------------------
def _clean_numeric(series: pd.Series) -> pd.Series:
    """Remove simbolos de moeda e converte para float."""
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
        "Valor Total", "Litros", "Preco por Litro",
        "Quilometragem", "KM Atual", "KM Anterior",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = _clean_numeric(df[col])
    # Tenta limpar Preco por Litro com acento tambem
    for col_name in ["Preço por Litro", "Preco por Litro"]:
        if col_name in df.columns:
            df[col_name] = _clean_numeric(df[col_name])
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
        st.error(f"Falha ao conectar a planilha: {exc}")
        return pd.DataFrame()

# ---------------------------------------------------------------------------
# 4. Sidebar - Navegacao & autenticacao
# ---------------------------------------------------------------------------
# -- Sidebar: perfil e senha ------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3408/3408506.png", width=90)
st.sidebar.title("Gestão de Combustível")
perfil = st.sidebar.selectbox("Modulo de Acesso", ["Motorista", "Gestor Administrativo"])
if "auth" not in st.session_state:
    st.session_state.auth = False
if perfil == "Gestor Administrativo":
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    if senha and senha == "admin123":
        st.session_state.auth = True
        st.sidebar.success("Acesso Autorizado")
    elif senha:
        st.session_state.auth = False
        st.sidebar.error("Senha incorreta")
# ---------------------------------------------------------------------------
# 5. Modulo Motorista
# ---------------------------------------------------------------------------
# == Modulo Motorista =======================================================
if perfil == "Motorista":
    st.title("Registro de Atividade")
    st.markdown("Clique no botao abaixo para registrar um novo abastecimento.")
    formulario_url = st.secrets.get("form_url", "https://forms.gle/e3tVoSTAFGGU3T787")
    st.link_button("ABRIR FORMULARIO DE ABASTECIMENTO", formulario_url)
    st.info("Apos enviar o formulario, os dados serao processados pela central.")
# ---------------------------------------------------------------------------
# 6. Modulo Gestor
# ---------------------------------------------------------------------------
# == Modulo Gestor ==========================================================
else:
    st.title("Painel de Controle Estrategico")
    if not st.session_state.auth:
        st.warning("Insira a senha para visualizar o painel.")
        st.stop()
    df = load_sheet_data()
    if df.empty:
        st.warning("Planilha vazia ou nao carregada. Verifique o conteudo.")
        st.stop()
    # Botao de atualizacao
    if st.sidebar.button("Atualizar dados"):
        st.cache_data.clear()
        st.rerun()
    # ── Filtros na sidebar ──────────────────────────────────────────────
    # -- Descobrir nomes de colunas com ou sem acento -----------------------
    def achar_col(df, *nomes):
        for n in nomes:
            if n in df.columns:
                return n
        return None
    col_veic = achar_col(df, "Veiculo", "Veículo", "veiculo", "veículo")
    col_plac = achar_col(df, "Placa", "placa")
    col_comb = achar_col(df, "Tipo Combustivel", "Tipo Combustível", "Combustivel", "Combustível")
    
    # -- Filtros na sidebar -------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filtros")
    
    def selectbox_col(df, col_veic, label, unique_key=None):
    # Garante que o df não está vazio e que a coluna realmente existe nele
    if df is not None and not df.empty and col_veic in df.columns:
        opts = ["Todos"] + sorted(df[col_veic].dropna().unique().tolist())
        return st.sidebar.selectbox(label, opts, key=unique_key)
    
    else:
        # Se a planilha estiver vazia ou a coluna não existir, mostra um aviso básico
        return st.sidebar.selectbox(label, ["Todos"], key=unique_key)
    
    # Veiculo
    if "Veiculo" in df.columns:
        opts_veic = ["Todos"] + sorted(df["Veiculo"].dropna().unique().tolist())
    elif "Veículo" in df.columns:
        opts_veic = ["Todos"] + sorted(df["Veículo"].dropna().unique().tolist())
    else:
        opts_veic = ["Todos"]
    filtro_veiculo = st.sidebar.selectbox("Veiculo", opts_veic)
    def selectbox_col(col_veic, label, unique_key=None):
            if col_veic:
                opts = ["Todos"] + sorted(df[col_veic].dropna().unique().tolist())
                return st.sidebar.selectbox(label, opts, key=unique_key)
    # Placa
    if "Placa" in df.columns:
        opts_placa = ["Todos"] + sorted(df["Placa"].dropna().unique().tolist())
    else:
        opts_placa = ["Todos"]
    filtro_placa = st.sidebar.selectbox("Placa", opts_placa)
    fv = selectbox_col(col_veic, "Veiculo", unique_key="filtro_veiculo_principal")
    fp = selectbox_col(col_plac, "Placa", unique_key="filtro_placa_principal")
    fc = selectbox_col(col_comb, "Combustivel", unique_key="filtro_combustivel_principal")
    
    # Combustivel
    if "Tipo Combustivel" in df.columns:
        opts_comb = ["Todos"] + sorted(df[col_comb].dropna().unique().tolist())         
    else:
        opts_comb = ["Todos"]
    filtro_combust = st.sidebar.selectbox("Combustivel", opts_comb)
    
    # Periodo de datas
    filtro_periodo = None
    if "Data" in df.columns:
        datas_validas = df["Data"].dropna()
        if not datas_validas.empty:
            data_min = datas_validas.min().date()
            data_max = datas_validas.max().date()
            filtro_periodo = st.sidebar.date_input(
                "Periodo",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max,
            )
    # ── Aplicar filtros ─────────────────────────────────────────────────
    # -- Aplicar filtros ----------------------------------------------------
    df_f = df.copy()
    if filtro_veiculo != "Todos" and col_veic and col_veic in df_f.columns:
        df_f = df_f[df_f[col_veic] == filtro_veiculo]
    if filtro_placa != "Todos" and "Placa" in df_f.columns:
        df_f = df_f[df_f["Placa"] == filtro_placa]
    if filtro_combust != "Todos" and col_comb and col_comb in df_f.columns:
        df_f = df_f[df_f[col_comb] == filtro_combust]
    if filtro_periodo and "Data" in df_f.columns and len(filtro_periodo) == 2:
        d0 = pd.Timestamp(filtro_periodo[0])
        d1 = pd.Timestamp(filtro_periodo[1])
        df_f = df_f[(df_f["Data"] >= d0) & (df_f["Data"] <= d1)]
    if "Data" in df_f.columns and "Valor Total" in df_f.columns:
        df_f = df_f.dropna(subset=["Data", "Valor Total"]).copy()
    # ── Tabela filtrada ─────────────────────────────────────────────────
    st.subheader(f"Registros filtrados  —  {len(df_f)} abastecimentos")
    # -- Tabela e download --------------------------------------------------
    st.dataframe(df_f, use_container_width=True)
    # ── Botao de download ───────────────────────────────────────────────
    csv_bytes = df_f.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="Baixar planilha filtrada (.csv)",
        data=csv_bytes,
        file_name="frota_filtrada.csv",
        mime="text/csv",
    )
    st.markdown("---")
    # ── KPIs ───────────────────────────────────────────────────────────
    has_v = "Valor Total" in df_f.columns
    has_l = "Litros" in df_f.columns
    k1, k2, k3, k4 = st.columns(4)
    if has_v:
        total_gasto = df_f["Valor Total"].sum()
        k1.metric("Gasto Total", f"R$ {total_gasto:,.2f}")
    if has_l:
        total_litros = df_f["Litros"].sum()
        k2.metric("Total Litros", f"{total_litros:,.1f} L")
    k3.metric("Abastecimentos", len(df_f))
    if has_v and has_l and df_f["Litros"].sum() > 0:
        custo_medio = df_f["Valor Total"].sum() / df_f["Litros"].sum()
        k4.metric("Custo Medio / L", f"R$ {custo_medio:,.2f}")
    st.markdown("---")
    # ── Graficos ────────────────────────────────────────────────────────
    # -- Graficos -----------------------------------------------------------
    if "Data" in df_f.columns and has_v and not df_f.empty:
        col_left, col_right = st.columns([2, 1])
        # Grafico 1: barras por DIA
        with col_left:
            diario = (
                df_f.groupby(df_f["Data"].dt.date)["Valor Total"]
                .sum()
                .reset_index()
                .rename(columns={"Data": "Dia"})
                .sort_values("Dia")
            )
            diario.columns = ["Dia", "Valor Total"]
            diario["Dia"] = diario["Dia"].astype(str)
            diario = diario.sort_values("Dia")
            fig1 = px.bar(
                diario,
                x="Dia",
                y="Valor Total",
                title="Gastos por Dia",
                color="Valor Total",
                color_continuous_scale="Teal",
                template="plotly_dark",
            )
            fig1.update_layout(
                xaxis_title="Data",
                yaxis_title="Valor (R$)",
                yaxis_tickprefix="R$ ",
                yaxis_tickformat=",.2f",
                coloraxis_showscale=False,
                xaxis_tickangle=-35,
            )
            fig1.update_traces(texttemplate="R$ %{y:,.2f}", textposition="outside")
            st.plotly_chart(fig1, use_container_width=True)
        # Grafico 2: pizza por combustivel
        with col_right:
            if col_comb and col_comb in df_f.columns:
                pc = df_f.groupby(col_comb)["Valor Total"].sum().reset_index()
                fig2 = px.pie(
                    pc,
                    names=col_comb,
                    values="Valor Total",
                    title="Gasto por Combustivel",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Teal,
                    template="plotly_dark",
                )
                fig2.update_traces(textinfo="percent+label")
                st.plotly_chart(fig2, use_container_width=True)
        # Grafico 3: barras por veiculo
        if col_veic and col_veic in df_f.columns:
            pv = (
                df_f.groupby(col_veic)["Valor Total"]
                .sum()
                .reset_index()
                .sort_values("Valor Total", ascending=False)
            )
            fig3 = px.bar(
                pv,
                x=col_veic,
                y="Valor Total",
                title="Gasto por Veiculo",
                color=col_veic,
                template="plotly_dark",
            )
            fig3.update_layout(
                yaxis_tickprefix="R$ ",
                yaxis_tickformat=",.2f",
                showlegend=False,
            )
            fig3.update_traces(texttemplate="R$ %{y:,.2f}", textposition="outside")
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Nenhum dado disponivel para os filtros selecionados.")
