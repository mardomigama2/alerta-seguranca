import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuração da página
st.set_page_config(
    page_title="Gestão de Alertas de Segurança",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Sistema de Análise e Alertas de Segurança")
st.markdown("Faça o upload da planilha de ocorrências para identificar os temas críticos e disparar os alertas da semana.")

# --- SIDEBAR: Configurações de E-mail ---
st.sidebar.header("📧 Configurações de Envio de E-mail")
enviar_email_real = st.sidebar.checkbox("Ativar envio real por e-mail", value=False)

if enviar_email_real:
    smtp_server = st.sidebar.text_input("Servidor SMTP", "smtp.gmail.com")
    smtp_port = st.sidebar.number_input("Porta SMTP", value=587)
    remetente_email = st.sidebar.text_input("E-mail Remetente")
    remetente_senha = st.sidebar.text_input("Senha / Token de App", type="password")
    destinatarios = st.sidebar.text_area("Destinatários (separados por vírgula)")

# --- UPLOAD DA PLANILHA ---
st.subheader("1. Enviar Planilha de Ocorrências")
uploaded_file = st.file_uploader("Arraste e solte o arquivo (.xlsx ou .csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Leitura do arquivo
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("Planilha carregada com sucesso!")
        
        # Seleção da coluna correspondente aos temas/ocorrências
        colunas = list(df.columns)
        coluna_tema = st.selectbox(
            "Selecione a coluna que contém o Tipo/Tema da Ocorrência:",
            options=colunas,
            index=0
        )

        if coluna_tema:
            # --- ANÁLISE TOP 3 ---
            st.divider()
            st.subheader("📊 Top 3 Temas com Mais Ocorrências")

            # Contagem de ocorrências
            contagem = df[coluna_tema].value_counts().reset_index()
            contagem.columns = ['Tema / Categoria', 'Quantidade']
            
            # Pega o Top 3
            top3 = contagem.head(3)
            
            # Exibe métricas em colunas
            cols = st.columns(3)
            for i, row in top3.iterrows():
                with cols[i]:
                    st.metric(
                        label=f"🥇 {i+1}º Lugar" if i==0 else (f"🥈 {i+2}º Lugar" if i==1 else f"🥉 {i+3}º Lugar"),
                        value=row['Tema / Categoria'],
                        delta=f"{row['Quantidade']} casos"
                    )

            # --- GERAÇÃO DOS ALERTAS DE SEGURANÇA ---
            st.divider()
            st.subheader("⚠️ Alertas de Segurança Gerados para a Semana")

            alertas = []
            for i, row in top3.iterrows():
                tema = row['Tema / Categoria']
                alerta_texto = f"**Foco em '{tema}':** Realizar inspeção diária sobre {tema.lower()} antes de iniciar as atividades. Certifique-se de que toda a equipe segue os procedimentos de prevenção."
                alertas.append((tema, alerta_texto))

            for idx, (tema, texto) in enumerate(alertas, 1):
                st.warning(f"**Alerta {idx} ({tema}):** {texto}")

            # --- MONTAGEM DO CORPO DO E-MAIL ---
            assunto_email = "🚨 Alerta Semanal de Segurança - Temas Críticos"
            corpo_email_html = f"""
            <h2>🚨 Alerta Semanal de Segurança do Trabalho</h2>
            <p>Com base no relatório de ocorrências mais recente, destacamos os 3 temas mais críticos para esta semana:</p>
            <ul>
            """
            for tema, texto in alertas:
                corpo_email_html += f"<li>{texto}</li>"
            
            corpo_email_html += """
            </ul>
            <p><strong>Ação exigida:</strong> Divulgar estes alertas nos Diálogos Diários de Segurança (DDS) durante a semana.</p>
            """

            # --- DISPARO DE E-MAIL ---
            st.divider()
            st.subheader("📬 Disparo do Alerta")

            if st.button("🚀 Disparar Alerta por E-mail para a Equipe"):
                if enviar_email_real:
                    if not remetente_email or not remetente_senha or not destinatarios:
                        st.error("Por favor, preencha todos os campos de e-mail na barra lateral.")
                    else:
                        try:
                            lista_destinatarios = [d.strip() for d in destinatarios.split(",")]
                            
                            msg = MIMEMultipart("alternative")
                            msg["Subject"] = assunto_email
                            msg["From"] = remetente_email
                            msg["To"] = ", ".join(lista_destinatarios)
                            msg.attach(MIMEText(corpo_email_html, "html"))

                            # Envio via SMTP
                            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                                server.starttls()
                                server.login(remetente_email, remetente_senha)
                                server.sendmail(remetente_email, lista_destinatarios, msg.as_string())

                            st.success(f"E-mails enviados com sucesso para: {', '.join(lista_destinatarios)}")
                        except Exception as e:
                            st.error(f"Falha ao enviar e-mail: {e}")
                else:
                    st.info("Simulação de Envio (Envio real desativado na barra lateral):")
                    st.code(corpo_email_html, language="html")
                    st.success("Alerta processado com sucesso!")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
else:
    st.info("Aguardando upload da planilha...")
