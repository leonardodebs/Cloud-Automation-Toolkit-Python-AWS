"""CloudTool CLI - Interface de Linha de Comando para Automação AWS"""

import typer
from typing import Optional
import json
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from cloudtool.ec2 import EC2Manager
from cloudtool.s3 import S3Manager
from cloudtool.reports import ReportGenerator

app = typer.Typer(
    name="cloudtool",
    help="CloudTool - Kit de Automação AWS",
    add_completion=False,
)

console = Console()


def print_json(data: dict):
    """Imprime dados como JSON formatado."""
    console.print_json(json.dumps(data, indent=2, default=str))


def print_table(data: list, title: str = ""):
    """Imprime dados como tabela."""
    if not data:
        console.print("[yellow]Nenhum dado encontrado[/yellow]")
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")

    if isinstance(data[0], dict):
        keys = list(data[0].keys())
        for key in keys:
            table.add_column(key.replace("_", " ").title())

        for item in data:
            table.add_row(*[str(item.get(key, "")) for key in keys])

    console.print(table)


@app.command()
def ec2(
    list_instances: bool = typer.Option(False, "--list", "-l", help="Lista todas as instâncias EC2"),
    start: Optional[str] = typer.Option(None, "--start", help="Inicia uma instância pelo ID"),
    stop: Optional[str] = typer.Option(None, "--stop", help="Para uma instância pelo ID"),
    create_snapshot: Optional[str] = typer.Option(None, "--snapshot", help="Cria snapshot a partir do ID do volume"),
    list_volumes: bool = typer.Option(False, "--volumes", help="Lista todos os volumes EBS"),
    state: Optional[str] = typer.Option(None, "--state", help="Filtrar instâncias por estado"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="Região AWS"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Perfil AWS"),
    output: str = typer.Option("table", "--output", "-o", help="Formato de saída (table/json)"),
):
    """Comandos de gerenciamento de instâncias EC2."""
    manager = EC2Manager(region=region, profile=profile)

    if list_instances:
        instances = manager.list_instances(state_filter=state)
        if output == "json":
            print_json({"instances": instances})
        else:
            print_table(instances, "Instâncias EC2")

    elif start:
        result = manager.start_instance(start)
        rprint(f"[green]Instância {start} iniciada com sucesso[/green]")
        if output == "json":
            print_json(result)

    elif stop:
        result = manager.stop_instance(stop)
        rprint(f"[green]Instância {stop} parada com sucesso[/green]")
        if output == "json":
            print_json(result)

    elif create_snapshot:
        result = manager.create_snapshot(create_snapshot)
        rprint(f"[green]Snapshot {result['snapshot_id']} criado com sucesso[/green]")
        if output == "json":
            print_json(result)

    elif list_volumes:
        volumes = manager.list_volumes()
        if output == "json":
            print_json({"volumes": volumes})
        else:
            print_table(volumes, "Volumes EBS")

    else:
        rprint("[yellow]Use --list, --start, --stop, --snapshot, ou --volumes[/yellow]")


@app.command()
def s3(
    list_buckets: bool = typer.Option(False, "--list", "-l", help="Lista todos os buckets S3"),
    upload: Optional[str] = typer.Option(None, "--upload", help="Faz upload de arquivo (formato: caminho_local:bucket[:chave])"),
    download: Optional[str] = typer.Option(None, "--download", help="Baixa arquivo (formato: bucket:chave:destino)"),
    sync: Optional[str] = typer.Option(None, "--sync", help="Sincroniza diretório para S3 (formato: dir_local:bucket[:prefixo])"),
    list_objects: Optional[str] = typer.Option(None, "--objects", help="Lista objetos em bucket"),
    clean_old: Optional[str] = typer.Option(None, "--clean", help="Limpa objetos antigos (formato: bucket:dias[:prefixo])"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="Região AWS"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Perfil AWS"),
    output: str = typer.Option("table", "--output", "-o", help="Formato de saída (table/json)"),
):
    """Comandos de gerenciamento de buckets S3."""
    manager = S3Manager(region=region, profile=profile)

    if list_buckets:
        buckets = manager.list_buckets()
        if output == "json":
            print_json({"buckets": buckets})
        else:
            print_table(buckets, "Buckets S3")

    elif upload:
        parts = upload.split(":")
        if len(parts) < 2:
            rprint("[red]Erro: Use o formato caminho_local:bucket[:chave][/red]")
            return
        file_path = parts[0]
        bucket = parts[1]
        key = parts[2] if len(parts) > 2 else None

        result = manager.upload_file(file_path, bucket, key)
        rprint(f"[green]Arquivo enviado para s3://{bucket}/{key or file_path}[/green]")
        if output == "json":
            print_json(result)

    elif download:
        parts = download.split(":")
        if len(parts) != 3:
            rprint("[red]Erro: Use o formato bucket:chave:destino[/red]")
            return
        bucket, key, destination = parts

        result = manager.download_file(bucket, key, destination)
        rprint(f"[green]Arquivo baixado para {destination}[/green]")
        if output == "json":
            print_json(result)

    elif sync:
        parts = sync.split(":")
        if len(parts) < 2:
            rprint("[red]Erro: Use o formato dir_local:bucket[:prefixo][/red]")
            return
        local_dir = parts[0]
        bucket = parts[1]
        prefix = parts[2] if len(parts) > 2 else ""

        result = manager.sync_directory(local_dir, bucket, prefix)
        rprint(f"[green]Sincronizados {result['uploaded']} arquivos para s3://{bucket}[/green]")
        if output == "json":
            print_json(result)

    elif list_objects:
        bucket = list_objects
        prefix = ""
        if ":" in bucket:
            parts = bucket.split(":")
            bucket = parts[0]
            prefix = parts[1]

        objects = manager.list_objects(bucket, prefix)
        if output == "json":
            print_json({"objects": objects})
        else:
            print_table(objects, f"Objetos em {bucket}")

    elif clean_old:
        parts = clean_old.split(":")
        if len(parts) < 2:
            rprint("[red]Erro: Use o formato bucket:dias[:prefixo][/red]")
            return
        bucket = parts[0]
        days = int(parts[1])
        prefix = parts[2] if len(parts) > 2 else ""

        result = manager.clean_old_objects(bucket, days, prefix)
        rprint(f"[green]Excluídos {result['deleted']} objetos de {bucket}[/green]")
        if output == "json":
            print_json(result)

    else:
        rprint("[yellow]Use --list, --upload, --download, --sync, --objects, ou --clean[/yellow]")


@app.command()
def reports(
    running_instances: bool = typer.Option(False, "--instances", "-i", help="Gera relatório de instâncias em execução"),
    storage: bool = typer.Option(False, "--storage", "-s", help="Gera relatório de uso de armazenamento"),
    cost: bool = typer.Option(False, "--cost", "-c", help="Gera relatório de estimativa de custos"),
    full: bool = typer.Option(False, "--full", "-f", help="Gera relatório completo de infraestrutura"),
    days: int = typer.Option(30, "--days", help="Número de dias para estimativa de custos"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="Região AWS"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Perfil AWS"),
    output: str = typer.Option("json", "--output", "-o", help="Formato de saída (table/json)"),
):
    """Gera relatórios de infraestrutura."""
    generator = ReportGenerator(region=region, profile=profile)

    if running_instances:
        report = generator.generate_running_instances_report()
        if output == "json":
            print_json(report)
        else:
            instances = report.get("instances", [])
            if instances:
                print_table(instances, f"Instâncias em Execução (Total: {report.get('total_instances')})")

    elif storage:
        report = generator.generate_storage_report()
        if output == "json":
            print_json(report)
        else:
            rprint(f"\n[bold]Relatório de Armazenamento[/bold]")
            rprint(f"Volumes EBS: {report['ebs_volumes']['count']} ({report['ebs_volumes']['total_size_gb']} GB)")
            rprint(f"Snapshots EBS: {report['ebs_snapshots']['count']} ({report['ebs_snapshots']['total_size_gb']} GB)")
            rprint(f"Buckets S3: {report['s3_buckets']['count']} ({report['s3_buckets']['total_size_gb']} GB)")
            rprint(f"[bold]Total: {report['total_storage_gb']} GB[/bold]")

    elif cost:
        report = generator.generate_cost_estimation_report(days=days)
        if output == "json":
            print_json(report)
        else:
            if "error" in report:
                rprint(f"[red]{report['error']}[/red]")
            else:
                rprint(f"\n[bold]Estimativa de Custos ({days} dias)[/bold]")
                rprint(f"Total: ${report['total_cost']} {report['currency']}")
                rprint(f"Média Diária: ${report['daily_average']}")
                if report.get("service_costs"):
                    print_table(report["service_costs"], "Custos por Serviço")

    elif full:
        report = generator.generate_full_report()
        print_json(report)

    else:
        rprint("[yellow]Use --instances, --storage, --cost, ou --full[/yellow]")


@app.command()
def rds(
    list_instances: bool = typer.Option(False, "--list", "-l", help="Lista instâncias RDS"),
    start: Optional[str] = typer.Option(None, "--start", help="Inicia uma instância pelo ID"),
    stop: Optional[str] = typer.Option(None, "--stop", help="Para uma instância pelo ID"),
    reboot: Optional[str] = typer.Option(None, "--reboot", help="Reinicia uma instância pelo ID"),
    snapshot: Optional[str] = typer.Option(None, "--snapshot", help="Cria snapshot (formato: instance_id[:snapshot_id])"),
    list_snapshots: bool = typer.Option(False, "--snapshots", help="Lista snapshots RDS"),
    state: Optional[str] = typer.Option(None, "--state", help="Filtrar por estado"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="Região AWS"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Perfil AWS"),
    output: str = typer.Option("table", "--output", "-o", help="Formato de saída"),
):
    """Comandos de gerenciamento RDS."""
    from cloudtool.rds import RDSManager
    manager = RDSManager(region=region, profile=profile)

    if list_instances:
        instances = manager.list_instances(state_filter=state)
        if output == "json":
            print_json({"instances": instances})
        else:
            print_table(instances, "Instâncias RDS")

    elif start:
        result = manager.start_instance(start)
        rprint(f"[green]Instância {start} iniciada[/green]")
        if output == "json":
            print_json(result)

    elif stop:
        result = manager.stop_instance(stop)
        rprint(f"[green]Instância {stop} parada[/green]")
        if output == "json":
            print_json(result)

    elif reboot:
        result = manager.reboot_instance(reboot)
        rprint(f"[green]Instância {reboot} reiniciada[/green]")
        if output == "json":
            print_json(result)

    elif snapshot:
        parts = snapshot.split(":")
        instance_id = parts[0]
        snapshot_id = parts[1] if len(parts) > 1 else None
        result = manager.create_snapshot(instance_id, snapshot_id)
        rprint(f"[green]Snapshot {result['snapshot_id']} criado[/green]")
        if output == "json":
            print_json(result)

    elif list_snapshots:
        instances = manager.list_snapshots(instance_id=state)
        if output == "json":
            print_json({"snapshots": instances})
        else:
            print_table(instances, "Snapshots RDS")

    else:
        rprint("[yellow]Use --list, --start, --stop, --reboot, --snapshot, ou --snapshots[/yellow]")


@app.command()
def iam(
    list_users: bool = typer.Option(False, "--users", "-u", help="Lista usuários IAM"),
    list_roles: bool = typer.Option(False, "--roles", help="Lista roles IAM"),
    list_policies: bool = typer.Option(False, "--policies", "-p", help="Lista políticas IAM"),
    list_groups: bool = typer.Option(False, "--groups", "-g", help="Lista grupos IAM"),
    list_profiles: bool = typer.Option(False, "--profiles", help="Lista instance profiles"),
    summary: bool = typer.Option(False, "--summary", "-s", help="Resumo da conta"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="Região AWS"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Perfil AWS"),
    output: str = typer.Option("table", "--output", "-o", help="Formato de saída"),
):
    """Comandos de gerenciamento IAM."""
    from cloudtool.iam import IAMManager
    manager = IAMManager(region=region, profile=profile)

    if list_users:
        users = manager.list_users()
        if output == "json":
            print_json({"users": users})
        else:
            print_table(users, "Usuários IAM")

    elif list_roles:
        roles = manager.list_roles()
        if output == "json":
            print_json({"roles": roles})
        else:
            print_table(roles, "Roles IAM")

    elif list_policies:
        policies = manager.list_policies()
        if output == "json":
            print_json({"policies": policies})
        else:
            print_table(policies, "Políticas IAM")

    elif list_groups:
        groups = manager.list_groups()
        if output == "json":
            print_json({"groups": groups})
        else:
            print_table(groups, "Grupos IAM")

    elif list_profiles:
        profiles = manager.list_instance_profiles()
        if output == "json":
            print_json({"profiles": profiles})
        else:
            print_table(profiles, "Instance Profiles")

    elif summary:
        result = manager.get_account_summary()
        if output == "json":
            print_json(result)
        else:
            rprint(f"\n[bold]Resumo da Conta IAM[/bold]")
            for key, value in result.items():
                rprint(f"{key}: {value}")

    else:
        rprint("[yellow]Use --users, --roles, --policies, --groups, --profiles, ou --summary[/yellow]")


@app.command()
def cloudwatch(
    list_alarms: bool = typer.Option(False, "--alarms", "-a", help="Lista alarmes CloudWatch"),
    list_metrics: bool = typer.Option(False, "--metrics", "-m", help="Lista métricas"),
    list_logs: bool = typer.Option(False, "--logs", help="Lista grupos de logs"),
    alarms: bool = typer.Option(False, "--alarm-state", help="Filtrar alarmes por estado"),
    log_group: Optional[str] = typer.Option(None, "--log-events", help="Eventos de log"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="Região AWS"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Perfil AWS"),
    output: str = typer.Option("table", "--output", "-o", help="Formato de saída"),
):
    """Comandos de gerenciamento CloudWatch."""
    from cloudtool.cloudwatch import CloudWatchManager
    manager = CloudWatchManager(region=region, profile=profile)

    if list_alarms:
        alarms_list = manager.list_alarms(state_filter=alarms)
        if output == "json":
            print_json({"alarms": alarms_list})
        else:
            print_table(alarms_list, "Alarmes CloudWatch")

    elif list_metrics:
        metrics = manager.list_metrics()
        if output == "json":
            print_json({"metrics": metrics})
        else:
            print_table(metrics, "Métricas CloudWatch")

    elif list_logs:
        groups = manager.list_log_groups()
        if output == "json":
            print_json({"log_groups": groups})
        else:
            print_table(groups, "Grup de Logs")

    elif log_group:
        events = manager.get_log_events(log_group, limit=50)
        if output == "json":
            print_json({"events": events})
        else:
            print_table(events, f"Eventos: {log_group}")

    else:
        rprint("[yellow]Use --alarms, --metrics, --logs, ou --log-events[/yellow]")


@app.command()
def ecr(
    list_repos: bool = typer.Option(False, "--list", "-l", help="Lista repositórios ECR"),
    list_images: Optional[str] = typer.Option(None, "--images", help="Lista imagens (repositório)"),
    describe: Optional[str] = typer.Option(None, "--describe", help="Descreve imagens"),
    token: bool = typer.Option(False, "--token", "-t", help="Obtém token ECR"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="Região AWS"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Perfil AWS"),
    output: str = typer.Option("table", "--output", "-o", help="Formato de saída"),
):
    """Comandos de gerenciamento ECR."""
    from cloudtool.ecr import ECRManager
    manager = ECRManager(region=region, profile=profile)

    if list_repos:
        repos = manager.list_repositories()
        if output == "json":
            print_json({"repositories": repos})
        else:
            print_table(repos, "Repositórios ECR")

    elif list_images:
        images = manager.list_images(list_images)
        if output == "json":
            print_json({"images": images})
        else:
            print_table(images, f"Imagens: {list_images}")

    elif describe:
        images = manager.describe_images(describe)
        if output == "json":
            print_json({"images": images})
        else:
            print_table(images, f"Imagens: {describe}")

    elif token:
        result = manager.get_authorization_token()
        rprint(f"[green]Token obtidos (use docker login)[/green]")
        if output == "json":
            print_json(result)

    else:
        rprint("[yellow]Use --list, --images, --describe, ou --token[/yellow]")


@app.command()
def version():
    """Mostra a versão do CloudTool."""
    from cloudtool import __version__
    rprint(f"[cyan]CloudTool v{__version__}[/cyan]")


if __name__ == "__main__":
    app()
