# CloudTool - Kit de Automação AWS

[![PyPI](https://img.shields.io/pypi/v/cloudtool)](https://pypi.org/project/cloudtool/)
[![Python](https://img.shields.io/python/pyversions/cloudtool)](https://pypi.org/project/cloudtool/)
[![License](https://img.shields.io/pypi/l/cloudtool)](LICENSE)

Uma ferramenta CLI abrangente para automatizar tarefas comuns de infraestrutura AWS. Construído com Python, Boto3 e Typer.

## Recursos

### Gerenciamento EC2
- Listar instâncias EC2 com filtragem por estado
- Iniciar/Parar instâncias
- Criar snapshots EBS
- Listar volumes EBS

### Gerenciamento S3
- Listar buckets S3 com metadados
- Upload de arquivos
- Download de arquivos
- Sincronizar diretórios locais com buckets
- Listar objetos em buckets
- Limpar objetos antigos (por idade)

### Gerenciamento RDS
- Listar instâncias RDS
- Iniciar/Parar/Reiniciar instâncias
- Criar snapshots de banco de dados
- Listar snapshots

### Gerenciamento IAM
- Listar usuários
- Listar roles
- Listar políticas
- Listar grupos
- Listar instance profiles
- Resumo da conta

### CloudWatch
- Listar alarmes
- Listar métricas
- Listar grupos de logs
- Obter eventos de logs

### ECR (Container Registry)
- Listar repositórios
- Listar imagens
- Obter token de autorização

### Relatórios
- Relatório de instâncias em execução
- Relatório de uso de armazenamento
- Estimativa de custos

### Dashboard Web
- Interface visual Streamlit
- Visão geral da infraestrutura
- Tabelas e métricas interativas

## Instalação

### Pré-requisitos
- Python 3.9+
- Credenciais AWS configuradas

### Instalar via pip

```bash
pip install cloudtool
```

### Instalar a partir do código-fonte

```bash
git clone https://github.com/leonardodebs/Cloud-Automation-Toolkit-Python-AWS.git
cd cloudtool

pip install -r requirements.txt
pip install -e .
```

## Configuração

### Credenciais AWS

Configure usando um dos métodos:

```bash
# AWS CLI (recomendado)
aws configure

# Variáveis de ambiente
export AWS_ACCESS_KEY_ID=sua-chave
export AWS_SECRET_ACCESS_KEY=sua-chave-secreta
export AWS_DEFAULT_REGION=us-east-1

# Perfil nomeado
export AWS_PROFILE=meu-perfil
```

## Uso

### Comandos Principais

```bash
# EC2
cloudtool ec2 --list
cloudtool ec2 --list --state running
cloudtool ec2 --start i-1234567890abcdef0
cloudtool ec2 --stop i-1234567890abcdef0
cloudtool ec2 --snapshot vol-1234567890abcdef0
cloudtool ec2 --volumes

# S3
cloudtool s3 --list
cloudtool s3 --upload arquivo.txt:meu-bucket
cloudtool s3 --download meu-bucket:chave:./arquivo.txt
cloudtool s3 --sync ./dir:meu-bucket
cloudtool s3 --objects meu-bucket
cloudtool s3 --clean meu-bucket:30

# RDS
cloudtool rds --list
cloudtool rds --start minha-db
cloudtool rds --stop minha-db
cloudtool rds --snapshots

# IAM
cloudtool iam --users
cloudtool iam --roles
cloudtool iam --policies
cloudtool iam --groups
cloudtool iam --summary

# CloudWatch
cloudtool cloudwatch --alarms
cloudtool cloudwatch --metrics
cloudtool cloudwatch --logs

# ECR
cloudtool ecr --list
cloudtool ecr --images meu-repo
cloudtool ecr --token

# Relatórios
cloudtool reports --instances
cloudtool reports --storage
cloudtool reports --cost
cloudtool reports --full
```

### Formato de Saída

```bash
# Tabela (padrão)
cloudtool ec2 --list --output table

# JSON
cloudtool ec2 --list --output json
```

### Specifies Região

```bash
cloudtool ec2 --list --region us-west-2
```

## Dashboard Web

O CloudTool inclui um dashboard web interativo:

```bash
streamlit run web_dashboard/app.py
```

Acesse: http://localhost:8501

## Uso Programático

```python
from cloudtool.ec2 import EC2Manager
from cloudtool.s3 import S3Manager
from cloudtool.rds import RDSManager
from cloudtool.iam import IAMManager
from cloudtool.reports import ReportGenerator

# EC2
ec2 = EC2Manager(region="us-east-1")
instances = ec2.list_instances()

# S3
s3 = S3Manager(region="us-east-1")
buckets = s3.list_buckets()

# RDS
rds = RDSManager(region="us-east-1")
databases = rds.list_instances()

# IAM
iam = IAMManager(region="us-east-1")
users = iam.list_users()

# Relatórios
reports = ReportGenerator(region="us-east-1")
report = reports.generate_running_instances_report()
```

## Desenvolvimento

### Executar Testes

```bash
pip install -e ".[dev]"
pytest
pytest --cov=cloudtool
```

### Qualidade de Código

```bash
flake8 cloudtool/
mypy cloudtool/
```

## Tecnologias

- **boto3** - SDK AWS para Python
- **typer** - Framework CLI
- **rich** - Formatação de saída
- **streamlit** - Dashboard web

## Licença

MIT License - consulte o arquivo [LICENSE](LICENSE)

## Autor

Cloud Engineer - leonardo@cloudengineer.dev