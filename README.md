# ☁️ CloudTool: AWS Automation Toolkit & Dashboard

<div align="center">

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Typer](https://img.shields.io/badge/Typer-000000?style=for-the-badge&logo=typer&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

**Uma solução robusta e elegante para orquestração de infraestrutura AWS via CLI e Dashboard Web.**

[Recursos](#-recursos) • [Instalação](#-instalação) • [Uso](#-uso) • [Dashboard](#-dashboard-web) • [Demo](#-modo-demonstração)

</div>

---

## 🏗️ Arquitetura do Sistema

![Cloud Automation Toolkit Architecture](docs/architecture.png)

O **CloudTool** foi desenvolvido para simplificar o dia a dia de Cloud Engineers e SREs. Ele combina a eficiência de uma interface de linha de comando (CLI) com a clareza visual de um Dashboard moderno, permitindo gerenciar recursos AWS com segurança e agilidade.

## ✨ Recursos Principais

### 🖥️ Gerenciamento EC2 & EBS
- Listagem inteligente de instâncias com filtros de estado.
- Operações de ciclo de vida (Start/Stop) em lote ou individuais.
- Gestão de snapshots EBS para backups rápidos.

### 🪣 Amazon S3 & Armazenamento
- Sincronização inteligente de diretórios (Local ↔ Cloud).
- Upload/Download simplificado de objetos.
- Políticas de limpeza automática por idade (Retention Policies).

### 🗄️ Database (RDS)
- Controle total sobre instâncias RDS (Start/Stop/Reboot).
- Geração de snapshots de banco de dados sob demanda.

### 👤 Segurança & Governança (IAM)
- Auditoria de usuários, roles e políticas.
- Resumo de segurança da conta e perfis de instância.

### 📈 Monitoramento & Logs (CloudWatch)
- Visualização de alarmes ativos e métricas críticas.
- Acesso rápido a Log Groups e streams de eventos.

### 🐳 Container Registry (ECR)
- Gestão de repositórios e imagens Docker.
- Autenticação simplificada para pipelines CI/CD.

## 🚀 Instalação

### Pré-requisitos
- Python 3.9 ou superior.
- Credenciais AWS configuradas (`~/.aws/credentials`).

### Setup Rápido
```bash
# Clone o repositório
git clone https://github.com/leonardodebs/Cloud-Automation-Toolkit-Python-AWS.git
cd Cloud-Automation-Toolkit-Python-AWS

# Instale as dependências
pip install -r requirements.txt

# Instale o pacote em modo editável
pip install -e .
```

## 📖 Como Usar

### Interface CLI
O CloudTool oferece comandos intuitivos e saída visual rica (tabelas e JSON):

```bash
# Listar instâncias EC2 em execução
cloudtool ec2 --list --state running

# Sincronizar diretório local com S3
cloudtool s3 --sync ./dist:meu-bucket-prod

# Gerar relatório completo de custos e recursos
cloudtool reports --full
```

### 📊 Dashboard Web
Para uma experiência visual completa, utilize o dashboard interativo:

```bash
streamlit run web_dashboard/app.py
```

## 🚀 Modo Demonstração (Novo!)
Deseja testar a interface ou tirar prints sem conectar a uma conta AWS real? 
Ative o **Modo Demonstração** diretamente na barra lateral do Dashboard. Ele carregará dados fictícios premium para visualização imediata.

## 🛠️ Stack Tecnológica

| Componente | Tecnologia |
| :--- | :--- |
| **Core** | Python 3.9+ |
| **AWS SDK** | Boto3 |
| **CLI Engine** | Typer & Rich |
| **Frontend** | Streamlit (High-Performance Dashboard) |
| **Data Ops** | Pandas |
| **Testes** | Pytest |

## 📄 Licença
Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---
<p align="center">
Desenvolvido por <b>Leonardo Debs</b><br>
<i>Cloud Engineer & Developer</i>
</p>