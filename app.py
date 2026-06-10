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
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados_nuvem():
    try:
        return conn.read(ttl=0) 
    except:
        return pd.DataFrame(columns=[
            "Data", "Motorista", "Veículo", "Placa", 
            "KM Atual", "Litros", "Valor Total", "Tipo Combustível"
        ])

# 3. INTERFACE LATERAL
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3408/3408506.png", width=100)
st.sidebar.title("Frota Inteligente")
perfil = st.sidebar.selectbox("Módulo de Acesso", ["Motorista", "Gestor Administrativo"])

# ---------------------------------------------------------
# MÓDULO MOTORISTA
# ---------------------------------------------------------
# ---------------------------------------------------------
# MÓDULO MOTORISTA (AGORA VIA GOOGLE FORMS)
# ---------------------------------------------------------
if perfil == "Motorista":
    st.title("⛽ Registro de Atividade")
    st.markdown("Clique no botão abaixo para registrar um novo abastecimento.")
    
    # Substitua o link abaixo pelo link real do seu formulário
    url_formulario = "https://docs.google.com/forms/d/sua-url-aqui"
    
    st.link_button("ABRIR FORMULÁRIO DE ABASTECIMENTO", url_formulario)
    
    st.info("Após enviar o formulário, os dados serão processados pela central.")

# ---------------------------------------------------------
# MÓDULO GESTOR
# ---------------------------------------------------------
else:
    st.title("📊 Painel de Controle Estratégico")
    
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    
    if senha == "admin123":
        st.sidebar.success("Acesso Autorizado")
        df = carregar_dados_nuvem()
        
        if df.empty:
            st.warning("Aguardando primeiros registros da frota.")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Gasto Total Acumulado", f"R$ {df['Valor Total'].sum():,.2f}")
            m2.metric("Média de Abastecimento", f"R$ {df['Valor Total'].mean():,.2f}")
            m3.metric("Veículos Ativos", df['Veículo'].nunique())
            
            st.markdown("### Análise de Custos por Veículo")
            fig = px.bar(df, x="Veículo", y="Valor Total", color="Tipo Combustível", 
                         template="plotly_dark", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Histórico de Lançamentos")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Exportar Dados para Excel (CSV)", csv, "relatorio_frota.csv", "text/csv")
            
    elif senha == "":
        st.warning("Por favor, insira a senha no menu lateral para visualizar os dados.")
    else:
        st.error("❌ Senha incorreta. O acesso ao painel de gestão é restrito.")
