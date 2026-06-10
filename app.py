import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Gestão de Combustível", layout="wide", initial_sidebar_state="expanded")

# Nome do arquivo onde os dados serão salvos
DATA_FILE = "dados_combustivel.csv"

# Função para carregar os dados
def carregar_dados():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "Data", "Motorista", "Veículo", "Placa", 
            "KM Atual", "Litros", "Valor Total", "Tipo Combustível"
        ])

# Função para salvar os dados
def salvar_dados(df):
    df.to_csv(DATA_FILE, index=False)

# Inicializa a base de dados
df_combustivel = carregar_dados()

# --- INTERFACE EXCLUSIVA (Menu Lateral) ---
st.sidebar.title("Sistema de Combustível")
perfil = st.sidebar.radio("Selecione seu perfil:", ["Motorista (Cadastro)", "Gestor (Relatórios)"])

# ---------------------------------------------------------
# 1. INTERFACE DO MOTORISTA
# ---------------------------------------------------------
if perfil == "Motorista (Cadastro)":
    st.header("⛽ Registro de Abastecimento")
    st.write("Preencha os dados do abastecimento realizado abaixo:")

    with st.form(key="form_abastecimento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            motorista = st.text_input("Nome do Motorista")
            veiculo = st.text_input("Modelo do Veículo (ex: Fiat Uno)")
            placa = st.text_input("Placa do Veículo").upper()
            tipo_comb = st.selectbox("Tipo de Combustível", ["Gasolina", "Etanol", "Diesel", "GNV"])
            
        with col2:
            km_atual = st.number_input("Quilometragem (KM) Atual", min_value=0, step=1)
            litros = st.number_input("Quantidade de Litros", min_value=0.0, step=0.1)
            valor_total = st.number_input("Valor Total Pago (R$)", min_value=0.0, step=0.1)
            data_abast = st.date_input("Data do Abastecimento", datetime.date.today())

        botao_enviar = st.form_submit_button("Salvar Abastecimento")

    if botao_enviar:
        if motorista and veiculo and placa and km_atual > 0 and litros > 0 and valor_total > 0:
            # Criar uma nova linha de dados
            novo_registro = pd.DataFrame([{
                "Data": data_abast.strftime("%Y-%m-%d"),
                "Motorista": motorista,
                "Veículo": veiculo,
                "Placa": placa,
                "KM Atual": km_atual,
                "Litros": litros,
                "Valor Total": valor_total,
                "Tipo Combustível": tipo_comb
            }])
            
            # Unir com os dados existentes e salvar
            df_combustivel = pd.concat([df_combustivel, novo_registro], ignore_index=True)
            salvar_dados(df_combustivel)
            st.success("✅ Dados registrados com sucesso!")
        else:
            st.error("❌ Por favor, preencha todos os campos corretamente.")

# ---------------------------------------------------------
# 2. INTERFACE DO GESTOR
# ---------------------------------------------------------
else:
    st.header("📊 Painel do Gestor (Dashboard)")
    
    if df_combustivel.empty:
        st.warning("Ainda não existem dados cadastrados pelos motoristas.")
    else:
        # Cálculos de Métricas Gerais
        total_gasto = df_combustivel["Valor Total"].sum()
        total_litros = df_combustivel["Litros"].sum()
        
        # Exibição de cartões de informação (Métricas)
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Gasto (R$)", f"R$ {total_gasto:,.2f}")
        m2.metric("Total de Litros", f"{total_litros:,.1f} L")
        m3.metric("Abastecimentos Realizados", len(df_combustivel))
        
        st.markdown("---")
        
        # Gráficos Comparativos
        st.subheader("Análise Visual")
        g1, g2 = st.columns(2)
        
        with g1:
            st.write("**Gasto Total por Veículo (R$)**")
            fig_gasto = px.bar(df_combustivel, x="Veículo", y="Valor Total", color="Tipo Combustível", barmode="group")
            st.plotly_chart(fig_gasto, use_container_width=True)
            
        with g2:
            st.write("**Evolução da Quilometragem por Veículo**")
            fig_km = px.line(df_combustivel, x="Data", y="KM Atual", color="Veículo", markers=True)
            st.plotly_chart(fig_km, use_container_width=True)
            
        st.markdown("---")
        
        # Tabela com dados completos
        st.subheader("Histórico Completo de Abastecimentos")
        st.dataframe(df_combustivel, use_container_width=True)
