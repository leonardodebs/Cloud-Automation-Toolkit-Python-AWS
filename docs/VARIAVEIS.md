# Variáveis de Ambiente - CloudTool

Este documento lista todas as variáveis de ambiente suportadas pelo CloudTool.

---

## Visão Geral

O CloudTool pode ser configurado via:
1. Variáveis de ambiente do sistema
2. Arquivo `.env` na raiz do projeto
3. Parâmetros de linha de comando

> **Nota:** Variables de ambiente têm precedência sobre valores padrão nos comandos.

---

## Variáveis Obrigatórias

### AWS Credentials

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `AWS_ACCESS_KEY_ID` | Chave de acesso AWS | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta AWS | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_DEFAULT_REGION` | Região AWS padrão | `us-east-1` |

```bash
# Recomendado: usar AWS CLI para configurar
aws configure

# Ou definir manualmente
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=us-east-1
```

---

## Variáveis Opcionais

### Configuração Geral

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CLOUDTOOL_OUTPUT` | `table` | Formato de saída (`table` ou `json`) |
| `CLOUDTOOL_TIMEOUT` | `120` | Timeout em segundos para operações |

### Perfil AWS

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `AWS_PROFILE` | Perfil nomeado do arquivo credentials | `production`, `development` |

```bash
# Usar perfil específico
export AWS_PROFILE=production

# Sobrescrever região
export AWS_DEFAULT_REGION=us-west-2
```

### S3 Específico

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `S3_MULTIPART_THRESHOLD` | `8388608` | Tamanho em bytes para multipart upload (5MB) |
| `S3_MULTIPART_CHUNKSIZE` | `52428800` | Tamanho de cada parte (50MB) |

### EC2 Específico

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `EC2_DEFAULT_REGION` | `us-east-1` | Região padrão para operações EC2 |

---

## Arquivo `.env.example`

Copie este template para `.env` na raiz do projeto:

```bash
# ============================================
# CloudTool - Configuração de Ambiente
# ============================================

# --------------------------------------------
# AWS Credentials
# --------------------------------------------
# NOTA: Recomendamos usar AWS CLI (aws configure)
# ou variáveis de ambiente do sistema

# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_DEFAULT_REGION=us-east-1
# AWS_PROFILE=

# --------------------------------------------
# Configuração Geral
# --------------------------------------------
# CLOUDTOOL_OUTPUT=table  # table | json
# CLOUDTOOL_TIMEOUT=120   # segundos

# --------------------------------------------
# S3 Específico
# --------------------------------------------
# S3_MULTIPART_THRESHOLD=8388608   # 5MB
# S3_MULTIPART_CHUNKSIZE=52428800  # 50MB

# --------------------------------------------
# EC2 Específico
# --------------------------------------------
# EC2_DEFAULT_REGION=us-east-1
```

---

## Configuração por Ambiente

### Desenvolvimento

```bash
# .env.desenvolvimento
AWS_PROFILE=dev
AWS_DEFAULT_REGION=us-east-1
CLOUDTOOL_OUTPUT=table
```

### Produção

```bash
# .env.producao
AWS_PROFILE=production
AWS_DEFAULT_REGION=us-east-1
CLOUDTOOL_OUTPUT=json
CLOUDTOOL_TIMEOUT=300
```

---

## Exemplos de Uso

### Com Variáveis de Ambiente

```bash
# Exportar variáveis
export AWS_DEFAULT_REGION=us-west-2
export AWS_PROFILE=my-profile

# Executar comandos
python -m cloudtool ec2 --list
python -m cloudtool s3 --list
python -m cloudtool reports --instances
```

### Com Arquivo .env

```bash
# Criar arquivo .env
cp .env.example .env
nano .env  # editar com suas credenciais

# Executar (variáveis carregadas automaticamente)
python -m cloudtool ec2 --list
```

---

## Precedência de Configuração

O CloudTool segue esta ordem de prioridade:

1. **Argumentos de linha de comando** (maior prioridade)
2. **Variáveis de ambiente do sistema**
3. **Arquivo `.env`**
4. **Valores padrão no código** (menor prioridade)

Exemplo:
```bash
# Região via CLI sobrescreve variável de ambiente
python -m cloudtool ec2 --list --region us-west-1

# JSON via CLI sobrescreve CLOUDTOOL_OUTPUT
python -m cloudtool ec2 --list --output json
```

---

## Segurança

### Não Commitar Credenciais

O arquivo `.env` está no `.gitignore` por padrão. Nunca commite credenciais reais.

```bash
# Verificar se .env está ignorado
cat .gitignore | grep -E "\.env"
```

### Usar IAM Roles (Recomendado)

Para instâncias EC2, use IAM Roles em vez de access keys:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "ec2:Describe*",
      "s3:ListBucket",
      "s3:GetObject",
      "s3:PutObject"
    ],
    "Resource": "*"
  }]
}
```

---

## Troubleshooting

### "Unable to locate credentials"

```bash
# Verificar variáveis definidas
env | grep AWS

# ou carregar do arquivo .env
source .env
```

### "The security token included in the request is invalid"

Credenciais expiradas ou role inválida. Atualizar credenciais:

```bash
aws sso login --profile production
# ou
aws configure
```

---

## Referências

- [Boto3 Session](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/session.html)
- [Environment Variables - AWS](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)
- [Python Dotenv](https://pypi.org/project/python-dotenv/)
