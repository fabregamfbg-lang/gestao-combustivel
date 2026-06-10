import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Gestão de Combustível", layout="wide")

# Inicializa os dados na memória (não precisa de arquivo externo)
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=[
        "Data", "Motorista", "Veículo", "Placa", 
        "KM Atual", "Litros", "Valor Total", "Tipo Combustível"
    ])

# Menu Lateral
st.sidebar.title("Sistema de Combustível")
perfil = st.sidebar.radio("Selecione seu perfil:", ["Motorista (Cadastro)", "Gestor (Relatórios)"])

# ---------------------------------------------------------
# 1. INTERFACE DO MOTORISTA
# ---------------------------------------------------------
if perfil == "Motorista (Cadastro)":
    st.header("⛽ Registro de Abastecimento")
    
    with st.form(key="form_abastecimento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            motorista = st.text_input("Nome do Motorista")
            veiculo = st.text_input("Modelo do Veículo")
            placa = st.text_input("Placa do Veículo").upper()
            tipo_comb = st.selectbox("Tipo de Combustível", ["Gasolina", "Etanol", "Diesel", "GNV"])
        with col2:
            km_atual = st.number_input("Quilometragem (KM) Atual", min_value=0, step=1)
            litros = st.number_input("Quantidade de Litros", min_value=0.0, step=0.1)
            valor_total = st.number_input("Valor Total Pago (R$)", min_value=0.0, step=0.1)
            data_abast = st.date_input("Data do Abastecimento", datetime.date.today())

        botao_enviar = st.form_submit_button("Salvar Abastecimento")

    if botao_enviar:
        if motorista and placa and km_atual > 0:
            novo_registro = pd.DataFrame([{
                "Data": data_abast,
                "Motorista": motorista,
                "Veículo": veiculo,
                "Placa": placa,
                "KM Atual": km_atual,
                "Litros": litros,
                "Valor Total": valor_total,
                "Tipo Combustível": tipo_comb
            }])
            st.session_state.dados = pd.concat([st.session_state.dados, novo_registro], ignore_index=True)
            st.success("✅ Abastecimento registrado!")
        else:
            st.error("Por favor, preencha os campos obrigatórios.")

# ---------------------------------------------------------
# 2. INTERFACE DO GESTOR
# ---------------------------------------------------------
else:
    st.header("📊 Painel do Gestor")
    
    if st.session_state.dados.empty:
        st.info("Nenhum dado cadastrado ainda.")
    else:
        df = st.session_state.dados
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Gasto Total", f"R$ {df['Valor Total'].sum():,.2f}")
        col2.metric("Total de Litros", f"{df['Litros'].sum():,.1f} L")
        col3.metric("Registros", len(df))
        
        # Gráfico
        st.subheader("Gasto por Veículo")
        fig = px.bar(df, x="Veículo", y="Valor Total", color="Tipo Combustível")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Histórico")
        st.dataframe(df)

        # Botão para zerar dados manualmente
        if st.button("Limpar todos os dados da sessão"):
            st.session_state.dados = pd.DataFrame(columns=[
                "Data", "Motorista", "Veículo", "Placa", 
                "KM Atual", "Litros", "Valor Total", "Tipo Combustível"
            ])
            st.rerun()
