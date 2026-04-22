"""Módulo de Gerenciamento de Instâncias EC2"""

import boto3
from typing import List, Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EC2Manager:
    """Gerencia instâncias EC2 para operações comuns."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """Inicializa o Gerenciador EC2.

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

    def list_instances(self, state_filter: Optional[str] = None) -> List[Dict]:
        """Lista instâncias EC2.

        Args:
            state_filter: Filtrar por estado da instância (running, stopped, etc.)

        Returns:
            Lista de dicionários de instâncias
        """
        try:
            params = {"Filters": [{"Name": "instance-state-code", "Values": ["0", "16", "32", "48", "64", "80"]}]}
            if state_filter:
                state_map = {"running": "16", "stopped": "80", "pending": "0", "shutting-down": "32", "terminated": "48", "stopping": "64"}
                if state_filter in state_map:
                    params["Filters"] = [{"Name": "instance-state-code", "Values": [state_map[state_filter]]}]

            response = self.ec2.describe_instances(**params)
            instances = []

            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append({
                        "instance_id": instance.get("InstanceId"),
                        "instance_type": instance.get("InstanceType"),
                        "state": instance.get("State", {}).get("Name"),
                        "public_ip": instance.get("PublicIpAddress"),
                        "private_ip": instance.get("PrivateIpAddress"),
                        "name": self._get_tag(instance, "Name"),
                        "ami_id": instance.get("ImageId"),
                        "launch_time": str(instance.get("LaunchTime")),
                        "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
                    })

            logger.info(f"Encontradas {len(instances)} instâncias")
            return instances

        except ClientError as e:
            logger.error(f"Erro ao listar instâncias: {e}")
            raise

    def _get_tag(self, instance: Dict, tag_name: str) -> str:
        """Obtém valor de tag da instância."""
        for tag in instance.get("Tags", []):
            if tag.get("Key") == tag_name:
                return tag.get("Value", "")
        return ""

    def start_instance(self, instance_id: str) -> Dict:
        """Inicia uma instância EC2.

        Args:
            instance_id: ID da instância para iniciar

        Returns:
            Dicionário com resultado da operação
        """
        try:
            self.ec2.start_instances(InstanceIds=[instance_id])
            logger.info(f"Iniciando instância: {instance_id}")
            return {"status": "success", "instance_id": instance_id, "action": "started"}

        except ClientError as e:
            logger.error(f"Erro ao iniciar instância {instance_id}: {e}")
            raise

    def stop_instance(self, instance_id: str, force: bool = False) -> Dict:
        """Para uma instância EC2.

        Args:
            instance_id: ID da instância para parar
            force: Forçar parada (necessário para instâncias sem shutdown adequado)

        Returns:
            Dicionário com resultado da operação
        """
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id], Force=force)
            logger.info(f"Parando instância: {instance_id}")
            return {"status": "success", "instance_id": instance_id, "action": "stopped"}

        except ClientError as e:
            logger.error(f"Erro ao parar instância {instance_id}: {e}")
            raise

    def create_snapshot(self, volume_id: str, description: Optional[str] = None) -> Dict:
        """Cria um snapshot de um volume EBS.

        Args:
            volume_id: ID do volume para criar snapshot
            description: Descrição opcional do snapshot

        Returns:
            Dicionário com informações do snapshot
        """
        try:
            if not description:
                description = f"Snapshot do volume {volume_id}"

            response = self.ec2.create_snapshot(
                VolumeId=volume_id,
                Description=description
            )

            logger.info(f"Snapshot criado: {response['SnapshotId']}")
            return {
                "snapshot_id": response["SnapshotId"],
                "volume_id": volume_id,
                "status": response["State"],
                "description": description
            }

        except ClientError as e:
            logger.error(f"Erro ao criar snapshot para volume {volume_id}: {e}")
            raise

    def list_volumes(self) -> List[Dict]:
        """Lista todos os volumes EBS.

        Returns:
            Lista de dicionários de volumes
        """
        try:
            response = self.ec2.describe_volumes()
            volumes = []

            for volume in response.get("Volumes", []):
                volumes.append({
                    "volume_id": volume.get("VolumeId"),
                    "size": volume.get("Size"),
                    "volume_type": volume.get("VolumeType"),
                    "state": volume.get("State"),
                    "availability_zone": volume.get("AvailabilityZone"),
                    "encrypted": volume.get("Encrypted"),
                })

            logger.info(f"Encontrados {len(volumes)} volumes")
            return volumes

        except ClientError as e:
            logger.error(f"Erro ao listar volumes: {e}")
            raise

    def get_instance_details(self, instance_id: str) -> Dict:
        """Obtém informações detalhadas sobre uma instância.

        Args:
            instance_id: ID da instância

        Returns:
            Dicionário com detalhes da instância
        """
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            reservations = response.get("Reservations", [])
            instances = reservations[0].get("Instances", []) if reservations else []

            if not instances:
                raise ValueError(f"Instância {instance_id} não encontrada")

            instance = instances[0]
            return {
                "instance_id": instance.get("InstanceId"),
                "instance_type": instance.get("InstanceType"),
                "state": instance.get("State", {}).get("Name"),
                "public_ip": instance.get("PublicIpAddress"),
                "private_ip": instance.get("PrivateIpAddress"),
                "name": self._get_tag(instance, "Name"),
                "ami_id": instance.get("ImageId"),
                "launch_time": str(instance.get("LaunchTime")),
                "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
                "vpc_id": instance.get("VpcId"),
                "subnet_id": instance.get("SubnetId"),
                "security_groups": [{"name": sg.get("GroupName"), "id": sg.get("GroupId")} for sg in instance.get("SecurityGroups", [])],
                "root_device": instance.get("RootDeviceName"),
                "root_device_type": instance.get("RootDeviceType"),
            }

        except ClientError as e:
            logger.error(f"Erro ao obter detalhes da instância: {e}")
            raise
