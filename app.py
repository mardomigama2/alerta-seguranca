import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from openai import OpenAI

# Configuração da página
st.set_page_config(
    page_title="Gestão de Alertas de Segurança",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Sistema de Análise e Alertas Individuais de Segurança")
st.markdown("Analise as ocorrências, defina o período e envie alertas focados (1 e-mail por tema) gerados por IA.")

# --- SIDEBAR: Configurações de IA e E-mail ---
st.sidebar.header("🤖 Configurações da IA (OpenAI)")
openai_api_key = st.sidebar.text_input("Chave da API OpenAI (API Key)", type="password", help="Insira sua chave sk-...")

st.sidebar.header("📧 Configurações de Envio de E-mail")
enviar_email_real = st.sidebar.checkbox("Ativar envio real por e-mail", value=False)

if enviar_email_real:
    smtp_server = st.sidebar.text_input("Servidor SMTP", "smtp.gmail.com")
    smtp_port = st.sidebar.number_input("Porta SMTP", value=587)
    remetente_email = st.sidebar.text_input("E-mail Remetente")
    remetente_senha = st.sidebar.text_input("Senha / Token de App", type="password")
    destinatarios = st.sidebar.text_area("Destinatários (separados por vírgula)")

# --- 1. DEFINIÇÃO DO PERÍODO ---
st.subheader("1. Período do Relatório")
col_d1, col_d2 = st.columns(2)
with col_d1:
    data_inicio = st.date_input("Data Inicial (y)", value=date.today())
with col_d2:
    data_fim = st.date_input("Data Final (z)", value=date.today())

data_inicio_str = data_inicio.strftime("%d/%m/%Y")
data_fim_str = data_fim.strftime("%d/%m/%Y")

# --- 2. UPLOAD DA PLANILHA ---
st.subheader("2. Enviar Planilha de Ocorrências")
uploaded_file = st.file_uploader("Arraste e solte o arquivo (.xlsx ou .csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("Planilha carregada com sucesso!")
        
        colunas = list(df.columns)
        coluna_tema = st.selectbox(
            "Selecione a coluna que contém o Tipo/Tema da Ocorrência:",
            options=colunas,
            index=0
        )

        if coluna_tema:
            total_ocorrencias = len(df)
            
            # --- ANÁLISE TOP 3 ---
            st.divider()
            st.subheader("📊 Top 3 Temas com Mais Ocorrências")

            contagem = df[coluna_tema].value_counts().reset_index()
            contagem.columns = ['Tema', 'Quantidade']
            
            top3 = contagem.head(3)
            
            cols = st.columns(3)
            for i, row in top3.iterrows():
                porcentagem = (row['Quantidade'] / total_ocorrencias) * 100
                with cols[i]:
                    st.metric(
                        label=f"🥇 {i+1}º Lugar" if i==0 else (f"🥈 {i+2}º Lugar" if i==1 else f"🥉 {i+3}º Lugar"),
                        value=row['Tema'],
                        delta=f"{row['Quantidade']} casos ({porcentagem:.1f}%)"
                    )

            # --- GERAÇÃO DOS ALERTAS COM IA ---
            st.divider()
            st.subheader("🤖 Alertas de Segurança Gerados por IA")

            alertas_gerados = []

            for i, row in top3.iterrows():
                tema = str(row['Tema'])
                pct = (row['Quantidade'] / total_ocorrencias) * 100
                pct_str = f"{pct:.1f}%"

                # Prompt para a IA aprimorar o texto mantendo a estrutura pedida
                prompt = f"""
                Você é um especialista em Segurança do Trabalho.
                Crie a mensagem do alerta de segurança mantendo RIGOROSAMENTE a estrutura abaixo, mas aprimorando os detalhes técnicos do tema {tema}:

                Estrutura obrigatória:
                "Os nossos registros mostram que {pct_str} das ocorrências registradas entre os dias {data_inicio_str} e {data_fim_str}, alerta sobre o tema {tema}. Por isso, importante abordar no seu DDS sobre esse tema. Considerar também um olhar focado sobre {tema} durante o Safety Tour e tratar sobre {tema} comportamento na abordagem comportamental."

                Instruções adicionais de melhoria da IA:
                Após a mensagem padrão acima, adicione exatamente 3 marcadores curtos e práticos (bullet points) com orientações técnicas específicas sobre o tema "{tema}" para apoiar o líder no DDS, no Safety Tour e na Abordagem Comportamental.
                Retorne o resultado final formatado de forma clara em HTML simples (use <p>, <ul>, <li> e <strong>).
                """

                # Chamada da IA ou fallback caso não haja chave da API
                if openai_api_key:
                    try:
                        client = OpenAI(api_key=openai_api_key)
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.7
                        )
                        texto_final_html = response.choices[0].message.content
                    except Exception as e:
                        st.error(f"Erro na IA para o tema '{tema}': {e}")
                        texto_final_html = f"""
                        <p>Os nossos registros mostram que <strong>{pct_str}</strong> das ocorrências registradas entre os dias <strong>{data_inicio_str}</strong> e <strong>{data_fim_str}</strong>, alerta sobre o tema <strong>{tema}</strong>. Por isso, importante abordar no seu DDS sobre esse tema. Considerar também um olhar focado sobre {tema} durante o Safety Tour e tratar sobre {tema} comportamento na abordagem comportamental.</p>
                        """
                else:
                    texto_final_html = f"""
                    <p>Os nossos registros mostram que <strong>{pct_str}</strong> das ocorrências registradas entre os dias <strong>{data_inicio_str}</strong> e <strong>{data_fim_str}</strong>, alerta sobre o tema <strong>{tema}</strong>. Por isso, importante abordar no seu DDS sobre esse tema. Considerar também um olhar focado sobre {tema} durante o Safety Tour e tratar sobre {tema} comportamento na abordagem comportamental.</p>
                    <p><em>(Insira sua chave OpenAI na barra lateral para gerar orientações automáticas avançadas de IA).</em></p>
                    """

                alertas_gerados.append({
                    "posicao": i + 1,
                    "tema": tema,
                    "porcentagem": pct_str,
                    "html": texto_final_html
                })

            # Exibe os 3 alertas na tela
            for item in alertas_gerados:
                with st.expander(f"⚠️ Alerta #{item['posicao']} - Tema: {item['tema']} ({item['porcentagem']})", expanded=True):
                    st.markdown(item['html'], unsafe_allow_html=True)

            # --- DISPARO DOS E-MAILS INDIVIDUAIS ---
            st.divider()
            st.subheader("📬 Disparo Automático (1 E-mail por Tema)")
            st.write("Ao clicar no botão abaixo, a plataforma enviará **3 e-mails independentes** para a equipe, um para cada tema em destaque.")

            if st.button("🚀 Disparar os 3 Alertas de Segurança Individuais por E-mail"):
                if enviar_email_real:
                    if not remetente_email or not remetente_senha or not destinatarios:
                        st.error("Por favor, preencha todos os campos de e-mail na barra lateral.")
                    else:
                        lista_destinatarios = [d.strip() for d in destinatarios.split(",")]
                        erros = 0
                        
                        for item in alertas_gerados:
                            assunto = f"🚨 Alerta de Segurança de Campo - Tema: {item['tema']}"
                            
                            corpo_html = f"""
                            <h2>🚨 Alerta de Segurança Semanal</h2>
                            {item['html']}
                            <hr>
                            <p><small>Este e-mail foi gerado e enviado automaticamente pelo Painel de Gestão de Segurança.</small></p>
                            """

                            try:
                                msg = MIMEMultipart("alternative")
                                msg["Subject"] = assunto
                                msg["From"] = remetente_email
                                msg["To"] = ", ".join(lista_destinatarios)
                                msg.attach(MIMEText(corpo_html, "html"))

                                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                                    server.starttls()
                                    server.login(remetente_email, remetente_senha)
                                    server.sendmail(remetente_email, lista_destinatarios, msg.as_string())

                                st.success(f"✅ E-mail do Alerta #{item['posicao']} ({item['tema']}) enviado com sucesso!")
                            except Exception as e:
                                st.error(f"❌ Erro ao enviar e-mail do tema '{item['tema']}': {e}")
                                erros += 1

                        if erros == 0:
                            st.balloons()
                else:
                    st.info("Simulação de Envio Ativa (Para enviar de verdade, marque 'Ativar envio real por e-mail' na barra lateral):")
                    for item in alertas_gerados:
                        st.subheader(f"E-mail {item['posicao']}: Tema - {item['tema']}")
                        st.code(item['html'], language="html")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("Aguardando upload da planilha...")
