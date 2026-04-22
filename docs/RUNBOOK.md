# Runbook: Operações do CloudTool

**Última atualização:** 2026-04-14  
**Responsável:** Time de Infraestrutura  
**Tempo estimado:** 5-15 minutos  
**Impacto:** Baixo (operações somente leitura), Alto (start/stop de instâncias)

---

## Objetivo

Documentar procedimentos operacionais para uso do CloudTool em operações de rotina e troubleshooting.

---

## Quando Usar

- Listar instâncias EC2 para verificação de ambiente
- Iniciar/parar instâncias para manutenção
- Upload de arquivos para buckets S3
- Limpeza de objetos antigos em buckets
- Geração de relatórios de infraestrutura

---

## Pré-requisitos

- [ ] Python 3.9+ instalado
- [ ] Credenciais AWS configuradas (`aws configure`)
- [ ] CloudTool instalado (`pip install -e .`)
- [ ] Permissões IAM adequadas para operação

---

## Procedimentos

### 1. Listar Instâncias EC2

**Objetivo:** Verificar instâncias existentes em uma região.

```bash
# Listar todas as instâncias
python -m cloudtool ec2 --list --region us-east-1

# Listar apenas instâncias em execução
python -m cloudtool ec2 --list --state running --region us-east-1

# Listar instâncias paradas
python -m cloudtool ec2 --list --state stopped --region us-east-1
```

**Saída esperada:**
```
┌──────────────────────────────┬────────────┬──────────┬────────────────┐
│ Instance Id                 │ Type       │ State    │ Name           │
├──────────────────────────────┼────────────┼──────────┼────────────────┤
│ i-0123456789abcdef0          │ t3.medium │ running │ web-server-01  │
│ i-9876543210fedcba          │ t3.small  │ stopped │ dev-server     │
└──────────────────────────────┴────────────┴──────────┴────────────────┘
```

**Verificação:** Saída com tabela de instâncias ou mensagem "Nenhum dado encontrado".

---

### 2. Iniciar uma Instância

**Objetivo:** Iniciar uma instância EC2 parada.

```bash
python -m cloudtool ec2 --start i-0123456789abcdef0 --region us-east-1
```

**Saída esperada:**
```
Instância i-0123456789abcdef0 iniciada com sucesso
```

**Verificação:**
```bash
python -m cloudtool ec2 --list --state running --region us-east-1
```

---

### 3. Parar uma Instância

**Objetivo:** Parar uma instância EC2 em execução.

```bash
python -m cloudtool ec2 --stop i-0123456789abcdef0 --region us-east-1
```

**Saída esperada:**
```
Instância i-0123456789abcdef0 parada com sucesso
```

**Atenção:** Dados em volumes EBS não persistentes (instance store) serão perdidos.

---

### 4. Criar Snapshot de Volume

**Objetivo:** Criar backup de um volume EBS.

```bash
python -m cloudtool ec2 --snapshot vol-0123456789abcdef0 --region us-east-1
```

**Saída esperada:**
```
Snapshot snap-0123456789abcdef0 criado com sucesso
```

**Verificação:**
```bash
aws ec2 describe-snapshots --snapshot-ids snap-0123456789abcdef0 --region us-east-1
```

---

### 5. Listar Buckets S3

**Objetivo:** Verificar buckets existentes.

```bash
python -m cloudtool s3 --list --region us-east-1
```

**Saída esperada:**
```
┌─────────────────────┬─────────────────────┬──────────┐
│ Name                │ Creation Date       │ Region   │
├─────────────────────┼─────────────────────┼──────────┤
│ meu-bucket-backup   │ 2026-01-15 10:30:00 │ us-east-1│
│ meu-bucket-app      │ 2026-02-20 14:22:00 │ us-west-2│
└─────────────────────┴─────────────────────┴──────────┘
```

---

### 6. Upload de Arquivo

**Objetivo:** Enviar arquivo para bucket S3.

```bash
python -m cloudtool s3 --upload ./arquivo.txt:meu-bucket --region us-east-1
```

**Saída esperada:**
```
Arquivo enviado para s3://meu-bucket/arquivo.txt
```

**Verificação:**
```bash
python -m cloudtool s3 --objects meu-bucket --region us-east-1
```

---

### 7. Sincronizar Diretório

**Objetivo:** Sincronizar pasta local com bucket S3.

```bash
python -m cloudtool s3 --sync ./uploads:meu-bucket/backup --region us-east-1
```

**Saída esperada:**
```
Sincronizados 10 arquivos para s3://meu-bucket/backup
```

---

### 8. Limpar Objetos Antigos

**Objetivo:** Remover objetos mais antigos que X dias.

```bash
# Limpar objetos com mais de 30 dias
python -m cloudtool s3 --clean meu-bucket:30 --region us-east-1

# Limpar objetos com mais de 7 dias em prefixo específico
python -m cloudtool s3 --clean meu-bucket:7:logs/ --region us-east-1
```

**Saída esperada:**
```
Excluídos 5 objetos de meu-bucket
```

**Atenção:** Operação irreversível. Recomenda-se testar com `--dry-run` primeiro (se implementado).

---

### 9. Gerar Relatório de Instâncias

**Objetivo:** Relatório de instâncias em execução.

```bash
python -m cloudtool reports --instances --region us-east-1
```

**Saída esperada:**
```
┌──────────────────────────────┬────────────┬────────┬────────────────┐
│ Instance Id                 │ Type       │ Vcpus  │ Memory Gb      │
├──────────────────────────────┼────────────┼────────┼────────────────┤
│ i-0123456789abcdef0          │ t3.medium  │ 2      │ 4              │
└──────────────────────────────┴────────────┴────────┴────────────────┘
Total: 1 instância, 2 vCPUs, 4 GB memória
```

---

### 10. Gerar Relatório de Armazenamento

**Objetivo:** Verificar uso de armazenamento.

```bash
python -m cloudtool reports --storage --region us-east-1
```

**Saída esperada:**
```
Relatório de Armazenamento
Volumes EBS: 5 (250 GB)
Snapshots EBS: 12 (180 GB)
Buckets S3: 3 (45 GB)
Total: 475 GB
```

---

### 11. Gerar Relatório de Custos

**Objetivo:** Verificar custos AWS.

```bash
# Últimos 30 dias
python -m cloudtool reports --cost --region us-east-1

# Últimos 7 dias
python -m cloudtool reports --cost --days 7 --region us-east-1
```

**Saída esperada:**
```
Estimativa de Custos (30 dias)
Total: $150.00 USD
Média Diária: $5.00
```

---

### 12. Saída JSON

**Objetivo:** Obter saída para processamento automatizado.

```bash
python -m cloudtool ec2 --list --output json --region us-east-1

python -m cloudtool s3 --list --output json --region us-east-1
```

---

## Troubleshooting

### Erro: "Unable to locate credentials"

**Causa:** Credenciais AWS não configuradas.

**Solução:**
```bash
aws configure
# ou
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCY
```

---

### Erro: "You are not authorized to perform this operation"

**Causa:** Permissões IAM insuficientes.

**Solução:** Adicionar política IAM adequada:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:CreateSnapshot",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Erro: "The bucket you are trying to access is not configured"

**Causa:** Region do bucket diferente da região especificada.

**Solução:** Especificar região correta do bucket:

```bash
python -m cloudtool s3 --list --region us-west-2
```

---

### Erro: "Cost Explorer not available"

**Causa:** Cost Explorer não habilitado na conta AWS.

**Solução:** Habilitar no console AWS em Billing → Cost Explorer.

---

## Rollback

### Reverter Parada de Instância

```bash
python -m cloudtool ec2 --start i-0123456789abcdef0 --region us-east-1
```

### Reverter Exclusão de Objetos S3

Objetos excluídos não podem ser recuperados automaticamente. Para recuperação:
1. Usar versão anterior do objeto (se versionamento habilitado)
2. Restaurar de backup externo
3. Contatar AWS Support

---

## Histórico de Execuções

| Data | Operação | Executado por | Resultado | Observações |
|------|----------|---------------|-----------|--------------|
| 2026-04-14 | Listar instâncias | admin | Sucesso | Verificação diária |
| 2026-04-14 | Limpar logs antigos | admin | Sucesso | 45 objetos removidos |
