import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA & ESTILIZAÇÃO CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Combustível",
    page_icon="⛽",
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
# 2. CONSTANTES, CONEXÃO & SECRETS
# ---------------------------------------------------------------------------
SHEET_URL = st.secrets.get(
    "gsheets_url",
    "https://docs.google.com/spreadsheets/d/1900KpIS6XXANllpWSqqVaUFkUFYXcvcGXW2cf3V6UDY/edit",
)

# Inicializa conexão de forma segura
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erro ao inicializar GSheetsConnection: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# 3. PIPELINE DE LIMPEZA E TRATAMENTO DE DADOS (ETL MÍNIMO)
# ---------------------------------------------------------------------------
def _clean_numeric(series: pd.Series) -> pd.Series:
    """Remove símbolos de moeda e formata strings para float numérico válido."""
    if series.dtype == object:
        series = (
            series.astype(str)
            .str.replace(r"[R$\s]", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
    return pd.to_numeric(series, errors="coerce")

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o Schema correto de dados necessário para os cálculos e KPIs."""
    df = df.copy()
    
    # Padronização de colunas numéricas críticas
    numeric_cols = [
        "Valor Total", "Litros", "Preco por Litro", "Preço por Litro",
        "Quilometragem", "KM Atual", "KM Anterior"
    ]
    for col in df.columns:
        if col in numeric_cols:
            df[col] = _clean_numeric(df[col])
            
    # Tratamento específico para Preço por Litro com acentuação alternada
    if "Preço por Litro" in df.columns and "Preco por Litro" not in df.columns:
        df["Preco por Litro"] = df["Preço por Litro"]

    # Normalização de Datas
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce").dt.normalize()
        
    return df

@st.cache_data(ttl=300)
def load_sheet_data() -> pd.DataFrame:
    """Consome a API do Google Sheets aplicando Cache inteligente de 5 minutos."""
    try:
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        return _clean_dataframe(df)
    except Exception as exc:
        st.error(f"Falha crítica ao conectar ou ler a planilha do Google: {exc}")
        return pd.DataFrame()

def achar_col(df, *nomes):
    """Mapeia dinamicamente colunas com variações de acentuação e caixa."""
    for n in nomes:
        if n in df.columns:
            return n
    return None

def selectbox_col(df, target_col, label, unique_key):
    """Gera um widget selectbox dinâmico isolando escopo para evitar duplicações."""
    if df is not None and not df.empty and target_col and target_col in df.columns:
        opts = ["Todos"] + sorted(df[target_col].dropna().unique().tolist())
        return st.sidebar.selectbox(label, opts, key=unique_key)
    return st.sidebar.selectbox(label, ["Todos"], key=unique_key)

# ---------------------------------------------------------------------------
# 4. SIDEBAR - NAVEGAÇÃO E AUTENTICAÇÃO DE ACESSO
# ---------------------------------------------------------------------------
st.sidebar.image("https://scontent.fpmw7-1.fna.fbcdn.net/v/t39.30808-6/273627335_101182425835277_7485276832228659162_n.png?stp=dst-png&cstp=mx1080x1080&ctp=s1080x1080&_nc_cat=105&ccb=1-7&_nc_sid=6ee11a&_nc_ohc=ivNAPsoTv2sQ7kNvwEqvdcO&_nc_oc=Adomvgqa6BxKjEVl79KUN-jsk4iGK3RJgOvDbpaFjgckCLkzpdW1XMhpayVbN2y_5-k&_nc_zt=23&_nc_ht=scontent.fpmw7-1.fna&_nc_gid=X75YFM-3tC2XHTm6b3e7PA&_nc_ss=7b289&oh=00_Af9ysk9XqA8U-ltwgunDRTyalmp10RK1l3FX-iemQsp0fA&oe=6A30B368", width=90)
st.sidebar.title("Gestão de Combustível")

perfil = st.sidebar.selectbox("Módulo de Acesso", ["Motorista", "Gestor Administrativo"])

if "auth" not in st.session_state:
    st.session_state.auth = False

if perfil == "Gestor Administrativo":
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    if senha == "admin123":
        st.session_state.auth = True
        st.sidebar.success("Acesso Autorizado")
    elif senha:
        st.session_state.auth = False
        st.sidebar.error("Senha incorreta")

# ---------------------------------------------------------------------------
# 5. MÓDULO MOTORISTA
# ---------------------------------------------------------------------------
if perfil == "Motorista":
    st.title("Registro de Atividade")
    st.markdown("Clique no botão abaixo para registrar um novo abastecimento de frota.")
    formulario_url = st.secrets.get("form_url", "https://forms.gle/e3tVoSTAFGGU3T787")
    st.link_button("ABRIR FORMULÁRIO DE ABASTECIMENTO", formulario_url)
    st.info("Após enviar os dados no formulário externo, o banco de dados será atualizado centralizadamente.")

# ---------------------------------------------------------------------------
# 6. MÓDULO GESTOR (DASHBOARD ANALÍTICO COMPLETO)
# ---------------------------------------------------------------------------
else:
    st.title("Painel de Controle Estratégico")
    
    if not st.session_state.auth:
        st.warning("Por favor, insira a credencial administrativa na barra lateral para visualizar os dados.")
        st.stop()
        
    df = load_sheet_data()
    
    if df.empty:
        st.warning("Aviso: A base de dados da planilha retornou vazia. Verifique a URL ou o preenchimento das abas.")
        st.stop()
        
    # Botão manual para forçar invalidação do cache de dados
    if st.sidebar.button("Atualizar Dados da Planilha"):
        st.cache_data.clear()
        st.rerun()
        
    # Mapeamento Inteligente de colunas flexíveis da Planilha do Cliente
    col_veic = achar_col(df, "Veiculo", "Veículo", "veiculo", "veículo")
    col_plac = achar_col(df, "Placa", "placa", "PLACA")
    col_comb = achar_col(df, "Tipo Combustivel", "Tipo Combustível", "Combustivel", "Combustível", "combustivel")
    
    # Interface de Filtros na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filtros de Busca")
    
    # Chamadas únicas e limpas da função construtora com chaves estritas
    fv = selectbox_col(df, col_veic, "Filtrar por Veículo", unique_key="sb_veiculo")
    fp = selectbox_col(df, col_plac, "Filtrar por Placa", unique_key="sb_placa")
    fc = selectbox_col(df, col_comb, "Filtrar por Combustível", unique_key="sb_combustivel")
    
    # Tratamento do Filtro de Intervalo Temporal (Período)
    filtro_periodo = None
    if "Data" in df.columns:
        datas_validas = df["Data"].dropna()
        if not datas_validas.empty:
            data_min = datas_validas.min().date()
            data_max = datas_validas.max().date()
            filtro_periodo = st.sidebar.date_input(
                "Período de Análise",
                value=(data_min, data_max),
                min_value=data_min,
                max_value=data_max,
            )

    # ---------------------------------------------------------------------------
    # 7. EXECUÇÃO DO MOTOR DE FILTRAGEM (PANDAS QUERY ENGINE)
    # ---------------------------------------------------------------------------
    df_f = df.copy()
    
    if fv != "Todos" and col_veic:
        df_f = df_f[df_f[col_veic] == fv]
        
    if fp != "Todos" and col_plac:
        df_f = df_f[df_f[col_plac] == fp]
        
    if fc != "Todos" and col_comb:
        df_f = df_f[df_f[col_comb] == fc]
        
    if filtro_periodo and "Data" in df_f.columns and len(filtro_periodo) == 2:
        d0 = pd.Timestamp(filtro_periodo[0])
        d1 = pd.Timestamp(filtro_periodo[1])
        df_f = df_f[(df_f["Data"] >= d0) & (df_f["Data"] <= d1)]
        
    # Limpa linhas fantasmas sem dados fundamentais para métricas
    if "Data" in df_f.columns and "Valor Total" in df_f.columns:
        df_f = df_f.dropna(subset=["Data", "Valor Total"]).copy()

    # ---------------------------------------------------------------------------
    # 8. RENDERIZAÇÃO DA VISUALIZAÇÃO DOS DADOS
    # ---------------------------------------------------------------------------
    st.subheader(f"Registros Filtrados — {len(df_f)} Abastecimentos Encontrados")
    st.dataframe(df_f, use_container_width=True)
    
    # Exportação de Dados em formato Amigável para Excel/BR (; e ,)
    csv_bytes = df_f.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="📥 Baixar Planilha Filtrada (.CSV)",
        data=csv_bytes,
        file_name="gestao_frota_filtrada.csv",
        mime="text/csv",
    )
    
    st.markdown("---")
    
    # ---------------------------------------------------------------------------
    # 9. CENTRAL DE KPIS COMPORTAMENTAIS
    # ---------------------------------------------------------------------------
    has_v = "Valor Total" in df_f.columns
    has_l = "Litros" in df_f.columns
    
    k1, k2, k3, k4 = st.columns(4)
    
    if has_v:
        total_gasto = df_f["Valor Total"].sum()
        k1.metric("Gasto Total", f"R$ {total_gasto:,.2f}")
    else:
        k1.metric("Gasto Total", "R$ 0,00")
        
    if has_l:
        total_litros = df_f["Litros"].sum()
        k2.metric("Total Litros Consumidos", f"{total_litros:,.1f} L")
    else:
        k2.metric("Total Litros Consumidos", "0.0 L")
        
    k3.metric("Qtd Abastecimentos", len(df_f))
    
    if has_v and has_l and df_f["Litros"].sum() > 0:
        custo_medio = df_f["Valor Total"].sum() / df_f["Litros"].sum()
        k4.metric("Preço Médio Pago por Litro", f"R$ {custo_medio:,.2f}")
    else:
        k4.metric("Preço Médio Pago por Litro", "R$ 0,00")
        
    st.markdown("---")

    # ---------------------------------------------------------------------------
    # 10. BLOCO DE BUSINESS INTELLIGENCE (GRÁFICOS PLOTLY)
    # ---------------------------------------------------------------------------
    if "Data" in df_f.columns and has_v and not df_f.empty:
        col_left, col_right = st.columns([2, 1])
        
        # G1: Evolução Temporal de Gastos Diários
        with col_left:
            diario = (
                df_f.groupby(df_f["Data"].dt.date)["Valor Total"]
                .sum()
                .reset_index()
                .rename(columns={"Data": "Dia"})
            )
            diario["Dia"] = diario["Dia"].astype(str)
            diario = diario.sort_values("Dia")
            
            fig1 = px.bar(
                diario,
                x="Dia",
                y="Valor Total",
                title="Histórico de Gastos Diários (R$)",
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
            
        # G2: Market Share Interno por Tipo de Combustível
        with col_right:
            if col_comb and col_comb in df_f.columns and not df_f[col_comb].empty:
                pc = df_f.groupby(col_comb)["Valor Total"].sum().reset_index()
                fig2 = px.pie(
                    pc,
                    names=col_comb,
                    values="Valor Total",
                    title="Distribuição por Combustível",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Teal,
                    template="plotly_dark",
                )
                fig2.update_traces(textinfo="percent+label")
                st.plotly_chart(fig2, use_container_width=True)
                
        # G3: Análise de Alocação de Recursos por Unidade Móvel (Veículo)
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
                title="Despesa Total por Veículo da Frota",
                color="Valor Total",
                color_continuous_scale="Teal",
                template="plotly_dark",
            )
            fig3.update_layout(
                xaxis_title="Veículo",
                yaxis_title="Gasto Acumulado (R$)",
                yaxis_tickprefix="R$ ",
                yaxis_tickformat=",.2f",
                coloraxis_showscale=False,
            )
            fig3.update_traces(texttemplate="R$ %{y:,.2f}", textposition="outside")
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("💡 Sem dados volumétricos suficientes para gerar gráficos comerciais neste intervalo.")
