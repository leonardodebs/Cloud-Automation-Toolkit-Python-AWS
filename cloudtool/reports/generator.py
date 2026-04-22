"""Módulo de Geração de Relatórios de Infraestrutura"""

import boto3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Gera relatórios de infraestrutura para recursos AWS."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """Inicializa o Gerador de Relatórios.

        Args:
            region: Região AWS (padrão: us-east-1)
            profile: Nome do perfil de credenciais AWS
        """
        self.region = region
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)

        self.ec2 = session.client("ec2")
        self.s3 = session.client("s3")
        self.ce = session.client("ce")

    def generate_running_instances_report(self) -> Dict:
        """Gera relatório de instâncias EC2 em execução.

        Returns:
            Dicionário contendo relatório de instâncias em execução
        """
        try:
            response = self.ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )

            instances = []
            total_vcpus = 0
            total_memory_gb = 0

            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_type = instance.get("InstanceType")
                    vcpus, memory = self._get_instance_type_specs(instance_type)

                    instance_info = {
                        "instance_id": instance.get("InstanceId"),
                        "name": self._get_tag(instance, "Name"),
                        "instance_type": instance_type,
                        "vcpus": vcpus,
                        "memory_gb": memory,
                        "public_ip": instance.get("PublicIpAddress"),
                        "private_ip": instance.get("PrivateIpAddress"),
                        "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
                        "launch_time": str(instance.get("LaunchTime")),
                    }
                    instances.append(instance_info)
                    total_vcpus += vcpus
                    total_memory_gb += memory

            return {
                "report_type": "running_instances",
                "generated_at": datetime.now().isoformat(),
                "region": self.region,
                "total_instances": len(instances),
                "total_vcpus": total_vcpus,
                "total_memory_gb": total_memory_gb,
                "instances": instances,
            }

        except ClientError as e:
            logger.error(f"Erro ao gerar relatório de instâncias em execução: {e}")
            raise

    def generate_storage_report(self) -> Dict:
        """Gera relatório de volumes EBS e snapshots.

        Returns:
            Dicionário contendo relatório de uso de armazenamento
        """
        try:
            volumes_response = self.ec2.describe_volumes()
            volumes = []

            total_volume_size_gb = 0
            total_volume_count = 0

            for volume in volumes_response.get("Volumes", []):
                vol_size = volume.get("Size", 0)
                vol_info = {
                    "volume_id": volume.get("VolumeId"),
                    "size_gb": vol_size,
                    "volume_type": volume.get("VolumeType"),
                    "state": volume.get("State"),
                    "availability_zone": volume.get("AvailabilityZone"),
                    "encrypted": volume.get("Encrypted"),
                }
                volumes.append(vol_info)
                total_volume_size_gb += vol_size
                total_volume_count += 1

            snapshots_response = self.ec2.describe_snapshots(OwnerIds=["self"])
            snapshots = []

            total_snapshot_size_gb = 0
            total_snapshot_count = 0

            for snapshot in snapshots_response.get("Snapshots", []):
                snap_size = snapshot.get("VolumeSize", 0)
                snap_info = {
                    "snapshot_id": snapshot.get("SnapshotId"),
                    "size_gb": snap_size,
                    "state": snapshot.get("State"),
                    "description": snapshot.get("Description", "")[:100],
                }
                snapshots.append(snap_info)
                total_snapshot_size_gb += snap_size
                total_snapshot_count += 1

            s3_buckets = self.s3.list_buckets().get("Buckets", [])
            total_s3_size_gb = 0

            for bucket in s3_buckets:
                try:
                    bucket_name = bucket.get("Name")
                    objects = self.s3.list_objects_v2(Bucket=bucket_name)
                    total_size = sum(obj.get("Size", 0) for obj in objects.get("Contents", []))
                    total_s3_size_gb += total_size / (1024**3)
                except ClientError:
                    pass

            total_s3_size_gb = round(total_s3_size_gb, 2)

            return {
                "report_type": "storage_usage",
                "generated_at": datetime.now().isoformat(),
                "region": self.region,
                "ebs_volumes": {
                    "count": total_volume_count,
                    "total_size_gb": total_volume_size_gb,
                    "volumes": volumes,
                },
                "ebs_snapshots": {
                    "count": total_snapshot_count,
                    "total_size_gb": total_snapshot_size_gb,
                    "snapshots": snapshots,
                },
                "s3_buckets": {
                    "count": len(s3_buckets),
                    "total_size_gb": total_s3_size_gb,
                },
                "total_storage_gb": round(total_volume_size_gb + total_snapshot_size_gb + total_s3_size_gb, 2),
            }

        except ClientError as e:
            logger.error(f"Erro ao gerar relatório de armazenamento: {e}")
            raise

    def generate_cost_estimation_report(self, days: int = 30) -> Dict:
        """Gera relatório de estimativa de custos.

        Args:
            days: Número de dias para buscar dados de custo

        Returns:
            Dicionário contendo relatório de estimativa de custos
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            response = self.ce.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d"),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost", "BlendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            service_costs = []
            total_cost = 0.0

            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    service = group.get("Keys", [""])[0]
                    cost = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", "0"))
                    if cost > 0:
                        service_costs.append({
                            "service": service,
                            "cost": round(cost, 2),
                            "currency": "USD",
                        })
                        total_cost += cost

            service_costs.sort(key=lambda x: x["cost"], reverse=True)

            return {
                "report_type": "cost_estimation",
                "generated_at": datetime.now().isoformat(),
                "period_start": start_date.strftime("%Y-%m-%d"),
                "period_end": end_date.strftime("%Y-%m-%d"),
                "days": days,
                "total_cost": round(total_cost, 2),
                "currency": "USD",
                "daily_average": round(total_cost / days, 2),
                "service_costs": service_costs,
            }

        except ClientError as e:
            logger.warning(f"Cost Explorer não disponível: {e}")
            return {
                "report_type": "cost_estimation",
                "error": "Cost Explorer não disponível. Certifique-se de que o faturamento está habilitado.",
                "generated_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de custos: {e}")
            raise

    def generate_full_report(self) -> Dict:
        """Gera relatório completo de infraestrutura.

        Returns:
            Dicionário contendo todos os relatórios
        """
        return {
            "full_report": {
                "generated_at": datetime.now().isoformat(),
                "region": self.region,
                "running_instances": self.generate_running_instances_report(),
                "storage": self.generate_storage_report(),
                "cost": self.generate_cost_estimation_report(),
            }
        }

    def _get_tag(self, instance: Dict, tag_name: str) -> str:
        """Obtém valor de tag da instância."""
        for tag in instance.get("Tags", []):
            if tag.get("Key") == tag_name:
                return tag.get("Value", "")
        return ""

    def _get_instance_type_specs(self, instance_type: str) -> tuple:
        """Obtém especificações de vCPU e memória para o tipo de instância."""
        specs = {
            "t2.micro": (1, 1), "t2.small": (1, 2), "t2.medium": (2, 4), "t2.large": (2, 8),
            "t3.micro": (2, 1), "t3.small": (2, 2), "t3.medium": (2, 4), "t3.large": (2, 8),
            "t4g.micro": (2, 1), "t4g.small": (2, 2), "t4g.medium": (2, 4), "t4g.large": (2, 8),
            "m5.large": (2, 8), "m5.xlarge": (4, 16), "m5.2xlarge": (8, 32), "m5.4xlarge": (16, 64),
            "m6i.large": (2, 8), "m6i.xlarge": (4, 16), "m6i.2xlarge": (8, 32), "m6i.4xlarge": (16, 64),
            "m7i.large": (2, 8), "m7i.xlarge": (4, 16), "m7i.2xlarge": (8, 32), "m7i.4xlarge": (16, 64),
            "c5.large": (2, 4), "c5.xlarge": (4, 8), "c5.2xlarge": (8, 16), "c5.4xlarge": (16, 32),
            "c6i.large": (2, 4), "c6i.xlarge": (4, 8), "c6i.2xlarge": (8, 16), "c6i.4xlarge": (16, 32),
            "c7i.large": (2, 4), "c7i.xlarge": (4, 8), "c7i.2xlarge": (8, 16), "c7i.4xlarge": (16, 32),
            "r5.large": (2, 16), "r5.xlarge": (4, 32), "r5.2xlarge": (8, 64), "r5.4xlarge": (16, 128),
            "r6i.large": (2, 16), "r6i.xlarge": (4, 32), "r6i.2xlarge": (8, 64), "r6i.4xlarge": (16, 128),
            "r7i.large": (2, 16), "r7i.xlarge": (4, 32), "r7i.2xlarge": (8, 64), "r7i.4xlarge": (16, 128),
            "i3.large": (2, 16), "i3.xlarge": (4, 32), "i3.2xlarge": (8, 64), "i3.4xlarge": (16, 128),
            "i4i.large": (2, 16), "i4i.xlarge": (4, 32), "i4i.2xlarge": (8, 64), "i4i.4xlarge": (16, 128),
            "d3.large": (2, 16), "d3.xlarge": (4, 32), "d3.2xlarge": (8, 64), "d3.4xlarge": (16, 128),
            "d3en.large": (2, 16), "d3en.xlarge": (4, 32), "d3en.2xlarge": (8, 64), "d3en.4xlarge": (16, 128),
            "p3.2xlarge": (8, 61), "p3.8xlarge": (32, 244), "p3.16xlarge": (64, 488),
            "p4d.24xlarge": (96, 1152), "p5.48xlarge": (192, 2048),
            "g4dn.xlarge": (4, 16), "g4dn.2xlarge": (8, 32), "g4dn.4xlarge": (16, 64), "g4dn.8xlarge": (32, 128),
            "g5.xlarge": (4, 16), "g5.2xlarge": (8, 32), "g5.4xlarge": (16, 64), "g5.8xlarge": (32, 128),
            "g6.xlarge": (4, 16), "g6.2xlarge": (8, 32), "g6.4xlarge": (16, 64), "g6.8xlarge": (32, 128),
            "inf1.xlarge": (4, 8), "inf1.2xlarge": (8, 16), "inf1.6xlarge": (24, 48),
            "inf2.xlarge": (4, 16), "inf2.2xlarge": (8, 32), "inf2.6xlarge": (24, 96), "inf2.24xlarge": (96, 384),
            "x2idn.16xlarge": (64, 1024), "x2idn.24xlarge": (96, 1536),
            "x2iedn.xlarge": (4, 128), "x2iedn.2xlarge": (8, 256), "x2iedn.4xlarge": (16, 512), "x2iedn.8xlarge": (32, 1024),
        }
        return specs.get(instance_type, (None, None))
