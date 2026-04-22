# Arquitetura do CloudTool

**Data:** 2026-04-14  
**Versão:** 1.0.0  
**Status:** Estável

---

## Visão Geral

O CloudTool é uma CLI modular para automação de tarefas comuns de infraestrutura AWS. A arquitetura segue o padrão de **camadas de abstração**, separando a interface de linha de comando (CLI) das operações de baixo nível com a AWS.

```
┌─────────────────────────────────────────────────────────┐
│                    CLI (Typer/Rich)                     │
│              cloudtool/cli.py                           │
├─────────────────────────────────────────────────────────┤
│                   Módulos de Gerenciamento              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ EC2Manager  │  │ S3Manager   │  │ ReportGenerator  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                   Camada AWS (Boto3)                    │
│              boto3.session (EC2, S3, CE)               │
├─────────────────────────────────────────────────────────┤
│                   Credenciais AWS                       │
│         Environment Variables / AWS Profiles           │
└─────────────────────────────────────────────────────────┘
```

---

## Componentes Principais

### 1. CLI (`cloudtool/cli.py`)

- **Framework:** Typer com Rich para formatação
- **Responsabilidade:** Parse de argumentos, formatação de saída (tabela/JSON)
- **Comandos:**
  - `ec2` — gerenciamento de instâncias
  - `s3` — gerenciamento de buckets e objetos
  - `reports` — geração de relatórios
  - `version` — versão da ferramenta

### 2. EC2 Manager (`cloudtool/ec2/manager.py`)

- **Responsabilidade:** Operações CRUD em instâncias EC2
- **Operações:**
  - `list_instances()` — lista instâncias com filtro por estado
  - `start_instance()` — inicia instância
  - `stop_instance()` — para instância
  - `create_snapshot()` — cria snapshot EBS
  - `list_volumes()` — lista volumes EBS

### 3. S3 Manager (`cloudtool/s3/manager.py`)

- **Responsabilidade:** Operações com buckets e objetos S3
- **Operações:**
  - `list_buckets()` — lista buckets com metadados
  - `upload_file()` — upload de arquivo único
  - `download_file()` — download de arquivo
  - `sync_directory()` — sincronização bidirecional
  - `list_objects()` — lista objetos em bucket
  - `clean_old_objects()` — remove objetos antigos

### 4. Report Generator (`cloudtool/reports/generator.py`)

- **Responsabilidade:** Geração de relatórios de infraestrutura
- **Relatórios:**
  - `generate_running_instances_report()` — instâncias em execução
  - `generate_storage_report()` — uso de armazenamento
  - `generate_cost_estimation_report()` — estimativa de custos
  - `generate_full_report()` — relatório completo

---

## Padrões de Design

### Singleton de Sessão AWS

Cada Manager cria sua própria sessão boto3:

```python
class EC2Manager:
    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)
        self.ec2 = session.client("ec2")
```

**Vantagens:**
- Suporte a múltiplos perfis AWS
- Configuração por região
- Reutilização de credenciais

### Tratamento de Erros

Erros são capturados e relançados com contexto:

```python
except ClientError as e:
    logger.error(f"Erro ao listar instâncias: {e}")
    raise
```

### Retorno Padronizado

Todas as operações retornam dicionários Python:

```python
# Sucesso
return {"status": "success", "instance_id": instance_id, "action": "started"}

# Erro
raise ClientError(...)
```

---

## Dependências

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| boto3 | >=1.34.0 | SDK AWS para Python |
| typer | >=0.12.0 | Framework CLI |
| rich | >=13.7.0 | Formatação de saída |
| python-dotenv | >=1.0.0 | Variáveis de ambiente |

---

## Fluxo de Execução

### Exemplo: Listar Instâncias EC2

```
1. Usuário executa: cloudtool ec2 --list --region us-east-1
         │
         ▼
2. cli.py parseia argumentos
         │
         ▼
3. EC2Manager(region="us-east-1") é instanciado
         │
         ▼
4. Session boto3 criada → cliente ec2
         │
         ▼
5. list_instances() chamada
         │
         ▼
6. API DescribeInstances chamada
         │
         ▼
7. Resposta transformada em lista de dicionários
         │
         ▼
8. Rich formata como tabela → output terminal
```

### Exemplo: Upload de Arquivo S3

```
1. cloudtool s3 --upload arquivo.txt:bucket
         │
         ▼
2. Validação de caminho local
         │
         ▼
3. S3Manager.upload_file() chamada
         │
         ▼
4. boto3 s3.upload_file() (multipart automático)
         │
         ▼
5. Log de sucesso
         │
         ▼
6. Retorno com metadados
```

---

## Configuração de Credenciais

### Precedência (ordem de prioridade)

1. **Parâmetro `profile`** — passed explicitly
2. **Variáveis de ambiente** — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
3. **Arquivo `~/.aws/credentials`** — configuração padrão
4. **IAM Role** — em instâncias EC2

### Variáveis Suportadas

```bash
# Região padrão
export AWS_DEFAULT_REGION=us-east-1

# Perfil nomeado
export AWS_PROFILE=production

# Credenciais explícitas
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Limitações e Considerações

### Rate Limiting

- Boto3 implementa retry automático com backoff exponencial
- Para uso intensivo, considerar Circuit Breaker

### Tamanho de Arquivos

- `upload_file()` usa multipart automaticamente para arquivos > 5MB
- Limite S3: 5GB por objeto

### Custo

- Relatórios de custo dependem do AWS Cost Explorer estar habilitado
- Operação é somente leitura (sem custo adicional)

---

## Extensibilidade

### Adicionar Novo Módulo

1. Criar `cloudtool/novo_modulo/manager.py`
2. Implementar classe com métodos
3. Exportar em `cloudtool/novo_modulo/__init__.py`
4. Adicionar comando em `cli.py`

### Adicionar Novo Relatório

1. Adicionar método em `ReportGenerator`
2. Retornar dicionário padronizado
3. Adicionar opção em `reports` command

---

## Referências

- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
