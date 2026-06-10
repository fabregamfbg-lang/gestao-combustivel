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
# Mude a conexão para esta forma direta:
# Substitua o link abaixo PELO LINK DA SUA PLANILHA (o link real do navegador)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1900KpIS6XXANllpWSqqVaUFkUFYXcvcGXW2cf3V6UDY/edit?gid=1425248762#gid=1425248762"

def carregar_dados_nuvem():
    try:
        # Lemos a planilha diretamente pelo link
        return conn.read(spreadsheet=SHEET_URL, ttl=0)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return pd.DataFrame()

# E certifique-se de que a conexão conn foi inicializada logo acima:
conn = st.connection("gsheets", type=GSheetsConnection)

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
    url_formulario = "https://forms.gle/e3tVoSTAFGGU3T787"
    
    st.link_button("ABRIR FORMULÁRIO DE ABASTECIMENTO", url_formulario)
    
    st.info("Após enviar o formulário, os dados serão processados pela central.")

# ---------------------------------------------------------
# MÓDULO GESTOR (VERSÃO DE DIAGNÓSTICO)
# ---------------------------------------------------------
else:
    st.title("📊 Painel de Controle Estratégico")
    
    senha = st.sidebar.text_input("Senha de Acesso", type="password")
    
    if senha == "admin123":
        st.sidebar.success("Acesso Autorizado")
        
        # Tenta ler a planilha e mostra o que ele encontrou
        try:
            df = conn.read(ttl=0)
            
            if df is None or df.empty:
                st.warning("O arquivo foi lido, mas a planilha está vazia.")
            else:
                st.success(f"Dados carregados! Total de linhas encontradas: {len(df)}")
                st.write("Colunas detectadas:", df.columns.tolist()) # Isso vai nos revelar o problema
                
                # Exibição dos dados
                st.dataframe(df)
                
                # Métricas e Gráficos (se as colunas baterem)
                if 'Valor Total' in df.columns:
                    st.metric("Gasto Total", f"R$ {df['Valor Total'].sum():,.2f}")
                else:
                    st.error("A coluna 'Valor Total' não foi encontrada. Verifique se o nome na planilha está idêntico.")
        
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")
            
    elif senha == "":
        st.warning("Insira a senha.")
    else:
        st.error("Senha incorreta.")
