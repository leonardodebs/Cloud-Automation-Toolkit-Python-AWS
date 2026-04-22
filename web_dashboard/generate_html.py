"""
Gera relatório HTML estático da infraestrutura AWS
Run: python web_dashboard/generate_html.py
"""
import boto3
from datetime import datetime


def get_aws_data():
    """Carrega dados da AWS."""
    session = boto3.Session()
    client = {}

    ec2 = session.client("ec2")
    s3 = session.client("s3")
    rds = session.client("rds")
    iam = session.client("iam")
    cw = session.client("cloudwatch")

    # EC2
    resp = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
    instances = []
    for res in resp.get("Reservations", []):
        for inst in res.get("Instances", []):
            instances.append({
                "id": inst.get("InstanceId"),
                "type": inst.get("InstanceType"),
                "name": next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), "N/A"),
            })
    client["ec2"] = instances

    # Volumes
    resp = ec2.describe_volumes()
    client["volumes"] = [{"id": v.get("VolumeId"), "size": v.get("Size"), "type": v.get("VolumeType")} for v in resp.get("Volumes", [])]

    # S3
    resp = s3.list_buckets()
    client["s3"] = [{"name": b.get("Name"), "created": b.get("CreationDate").strftime("%Y-%m-%d")} for b in resp.get("Buckets", [])]

    # RDS
    resp = rds.describe_db_instances()
    client["rds"] = [{"id": db.get("DBInstanceIdentifier"), "type": db.get("DBInstanceClass"), "engine": db.get("Engine")} for db in resp.get("DBInstances", [])]

    # IAM
    users = iam.list_users().get("Users", [])
    roles = iam.list_roles().get("Roles", [])
    groups = iam.list_groups().get("Groups", [])
    client["iam_users"] = [u.get("UserName") for u in users]
    client["iam_roles"] = [r.get("RoleName") for r in roles]
    client["iam_groups"] = [g.get("GroupName") for g in groups]

    # CloudWatch
    alarms = cw.describe_alarms().get("MetricAlarms", [])
    client["alarms"] = [{"name": a.get("AlarmName"), "state": a.get("StateValue")} for a in alarms]

    return client


def generate_html(data):
    """Gera HTML."""
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudTool Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; }}
        .header {{ background: #161b22; padding: 20px 40px; border-bottom: 1px solid #30363d; }}
        .header h1 {{ color: #58a6ff; font-size: 24px; }}
        .header .subtitle {{ color: #8b949e; font-size: 14px; margin-top: 4px; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px 40px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }}
        .metric-card .value {{ font-size: 32px; font-weight: 600; color: #58a6ff; }}
        .metric-card .label {{ font-size: 14px; color: #8b949e; margin-top: 4px; }}
        .section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 20px; }}
        .section-header {{ padding: 16px 20px; border-bottom: 1px solid #30363d; }}
        .section-header h2 {{ font-size: 16px; color: #c9d1d9; }}
        .section-content {{ padding: 16px 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #30363d; }}
        th {{ color: #8b949e; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        td {{ font-size: 14px; }}
        tr:last-child td {{ border-bottom: none; }}
        .empty {{ color: #8b949e; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>☁️ CloudTool Dashboard</h1>
        <div class="subtitle">Infraestrutura AWS · {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>
    <div class="container">
        <div class="metrics">
            <div class="metric-card">
                <div class="value">{len(data['ec2'])}</div>
                <div class="label">EC2 Rodando</div>
            </div>
            <div class="metric-card">
                <div class="value">{len(data['s3'])}</div>
                <div class="label">S3 Buckets</div>
            </div>
            <div class="metric-card">
                <div class="value">{len(data['rds'])}</div>
                <div class="label">RDS</div>
            </div>
            <div class="metric-card">
                <div class="value">{len(data['iam_users'])}</div>
                <div class="label">IAM Usuários</div>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>🖥️ EC2 Instâncias</h2></div>
            <div class="section-content">
                <table>
                    <thead><tr><th>ID</th><th>Nome</th><th>Tipo</th></tr></thead>
                    <tbody>
                        {''.join(f"<tr><td>{i['id']}</td><td>{i['name']}</td><td>{i['type']}</td></tr>" for i in data['ec2']) or '<tr><td colspan="3" class="empty">Nenhuma instância em execução</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>🪣 S3 Buckets</h2></div>
            <div class="section-content">
                <table>
                    <thead><tr><th>Nome</th><th>Criado em</th></tr></thead>
                    <tbody>
                        {''.join(f"<tr><td>{b['name']}</td><td>{b['created']}</td></tr>" for b in data['s3']) or '<tr><td colspan="2" class="empty">Nenhum bucket</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>🗄️ RDS</h2></div>
            <div class="section-content">
                <table>
                    <thead><tr><th>ID</th><th>Tipo</th><th>Engine</th></tr></thead>
                    <tbody>
                        {''.join(f"<tr><td>{r['id']}</td><td>{r['type']}</td><td>{r['engine']}</td></tr>" for r in data['rds']) or '<tr><td colspan="3" class="empty">Nenhuma instância RDS</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>👤 IAM</h2></div>
            <div class="section-content">
                <table>
                    <thead><tr><th>Usuários</th><th>Roles</th><th>Grupos</th></tr></thead>
                    <tbody>
                        <tr><td>{', '.join(data['iam_users']) or '-'}</td><td>{', '.join(data['iam_roles']) or '-'}</td><td>{', '.join(data['iam_groups']) or '-'}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><h2>🔔 CloudWatch Alarmes</h2></div>
            <div class="section-content">
                <table>
                    <thead><tr><th>Nome</th><th>Estado</th></tr></thead>
                    <tbody>
                        {''.join(f"<tr><td>{a['name']}</td><td>{a['state']}</td></tr>" for a in data['alarms']) or '<tr><td colspan="2" class="empty">Nenhum alarme</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""
    return html


if __name__ == "__main__":
    print(" Coletando dados da AWS...")
    data = get_aws_data()
    html = generate_html(data)
    
    output = "web_dashboard/report.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f" Relatório gerado: {output}")
    print(" Abra no navegador!")