import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA (VISUAL PROFISSIONAL)
st.set_page_config(page_title="Frota Inteligente Pro", layout="wide")

# CSS para melhorar o visual (Estilo Dark Corporate)
st.markdown("""
    <style>
    .main { background-color: #0f172a; }
    .stMetric { background-color: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155; }
    .stButton>button { background-color: #10b981; color: white; border-radius: 10px; width: 100%; }
    .stTextInput>div>div>input { background-color: #1e293b; color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
# Nota: Você precisará configurar o URL da planilha nos Secrets do Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_nuvem():
    try:
        # Tenta ler os dados. Se a planilha estiver vazia, retorna DF vazio
        return conn.read(ttl=0) 
    except:
        return pd.DataFrame(columns=[
            "Data", "Motorista", "Veículo", "Placa", 
            "KM Atual", "Litros", "Valor Total", "Tipo Combustível"
        ])

# 3. INTERFACE LATERAL (ROLE-BASED ACCESS)
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3408/3408506.png", width=100)
st.sidebar.title("Frota Inteligente")
perfil = st.sidebar.selectbox("Módulo de Acesso", ["Motorista", "Gestor Administrativo"])

# ---------------------------------------------------------
# MÓDULO MOTORISTA (SIMPLES E DIRETO)
# ---------------------------------------------------------
if perfil == "Motorista":
    st.title("⛽ Registro de Atividade")
    st.info("Preencha os dados com atenção. O registro é enviado diretamente à central.")
    
    with st.form("abastecimento"):
        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Motorista")
            veiculo = st.text_input("Veículo (Modelo)")
            placa = st.text_input("Placa").upper()
        with c2:
            km = st.number_input("Quilometragem Atual", min_value=0)
            valor = st.number_input("Valor Total (R$)", min_value=0.0)
            comb = st.selectbox("Combustível", ["Diesel", "Gasolina", "Etanol", "GNV"])
        
        data = st.date_input("Data")
        submit = st.form_submit_button("ENVIAR DADOS")

    if submit:
        if nome and placa and km > 0:
            # Lógica para salvar no Google Sheets
            df_existente = carregar_dados_nuvem()
            novo_dado = pd.DataFrame([[data.strftime("%Y-%m-%d"), nome, veiculo, placa, km, 0, valor, comb]], 
                                     columns=df_existente.columns)
            df_final = pd.concat([df_existente, novo_dado], ignore_index=True)
            conn.update(data=df_final)
            st.success("✅ Dados enviados com sucesso!")
        else:
            st.warning("⚠️ Preencha todos os campos obrigatórios.")

# ---------------------------------------------------------
# MÓDULO GESTOR (PROTEGIDO POR SENHA)
# ---------------------------------------------------------
else:
    st.title("📊 Painel de Controle Estratégico")
    
    # CONTROLE DE ACESSO
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    
    if senha == "admin123": # Altere para sua senha preferida
        st.sidebar.success("Acesso Autorizado")
        
        df = carregar_dados_nuvem()
        
        if df.empty:
            st.warning("Aguardando primeiros registros da frota.")
        else:
            # MÉTRICAS EM CARTÕES PROFISSIONAIS
            m1, m2, m3 = st.columns(3)
            m1.metric("Gasto Total Acumulado", f"R$ {df['Valor Total'].sum():,.2f}")
            m2.metric("Média de Abastecimento", f"R$ {df['Valor Total'].mean():,.2f}")
            m3.metric("Veículos Ativos", df['Veículo'].nunique())
            
            # GRÁFICOS
            st.markdown("### Análise de Custos por Veículo")
            fig = px.bar(df, x="Veículo", y="Valor Total", color="Tipo Combustível", 
                         template="plotly_dark", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Histórico de Lançamentos")
            st.dataframe(df, use_container_width=True)
            
            # DOWNLOAD
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Exportar Dados para Excel (CSV)", csv, "relatorio_frota.csv", "text/csv")
            
    elif senha == "":
        st.warning("Por favor, insira a senha no menu lateral para visualizar os dados.")
    else:
        st.error("❌ Senha incorreta. O acesso ao painel de gestão é restrito.")

### Passo 2: Como conectar a Planilha do Google

Como você não entende de programação, siga este guia visual simplificado:

1.  **Crie a Planilha:** No seu Google Drive, crie uma planilha e chame-a de `Dados_Frota`. Na primeira linha, coloque exatamente estes nomes nas colunas: `Data`, `Motorista`, `Veículo`, `Placa`, `KM Atual`, `Litros`, `Valor Total`, `Tipo Combustível`.
2.  **Torne-a Pública (Para Teste Inicial):** Clique em **Compartilhar** -> **Qualquer pessoa com o link** -> **Editor**. Copie o link da planilha.
3.  **Configuração no Streamlit Cloud:**
    *   No painel do seu app no Streamlit Cloud, vá em **Settings** -> **Secrets**.
    *   Cole o seguinte código lá (substituindo pelo seu link):
        ```toml
        public_gsheets_url = "COLE_AQUI_O_LINK_DA_SUA_PLANILHA"
        4.  **No arquivo `requirements.txt` do GitHub, adicione:**
    ```text
    streamlit
    pandas
    plotly
    st-gsheets-connection
    
Dessa forma, o seu aplicativo se torna uma ferramenta profissional: os dados não somem, o visual impressiona os gestores e você garante que motoristas não vejam informações financeiras sigilosas!

O que achou deste novo visual e da estrutura de segurança? Se estiver pronto, podemos avançar para os testes reais!
