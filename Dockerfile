# Use uma imagem base leve de Python
FROM python:3.11-slim

# Evita que o Python gere arquivos .pyc e permite que os logs apareçam imediatamente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para algumas bibliotecas Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .
COPY pyproject.toml .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir .

# Copia o restante do código do projeto
COPY cloudtool/ ./cloudtool/
COPY web_dashboard/ ./web_dashboard/

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Cria o diretório de configuração do Streamlit
RUN mkdir -p ~/.streamlit

# Configura o Streamlit para rodar sem abrir o navegador e na porta correta
RUN echo "\
[server]\n\
headless = true\n\
port = 8501\n\
enableCORS = false\n\
\n\
[theme]\n\
primaryColor = '#FF4B4B'\n\
backgroundColor = '#0E1117'\n\
secondaryBackgroundColor = '#262730'\n\
textColor = '#FAFAFA'\n\
font = 'sans serif'\n\
" > ~/.streamlit/config.toml

# Comando para iniciar o dashboard
ENTRYPOINT ["streamlit", "run", "web_dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
