"""Módulo de Gerenciamento de Instâncias RDS"""

import boto3
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RDSManager:
    """Gerencia instâncias RDS para operações comuns."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """Inicializa o Gerenciador RDS.

        Args:
            region: Região AWS (padrão: us-east-1)
            profile: Nome do perfil de credenciais AWS
        """
        self.region = region
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)
        self.rds = session.client("rds")

    def list_instances(self, state_filter: Optional[str] = None) -> List[Dict]:
        """Lista instâncias RDS.

        Args:
            state_filter: Filtrar por estado (available, stopped, etc)

        Returns:
            Lista de dicionários de instâncias
        """
        try:
            params = {}
            if state_filter:
                params["Filters"] = [{"Name": "db-instance-state", "Values": [state_filter]}]

            response = self.rds.describe_db_instances(**params)
            instances = []

            for db in response.get("DBInstances", []):
                instances.append({
                    "instance_id": db.get("DBInstanceIdentifier"),
                    "instance_type": db.get("DBInstanceClass"),
                    "engine": db.get("Engine"),
                    "engine_version": db.get("EngineVersion"),
                    "state": db.get("DBInstanceStatus"),
                    "endpoint": db.get("Endpoint", {}).get("Address"),
                    "port": db.get("Endpoint", {}).get("Port"),
                    "allocated_storage": db.get("AllocatedStorage"),
                    "storage_type": db.get("StorageType"),
                    "master_username": db.get("MasterUsername"),
                    "database_name": db.get("DatabaseName"),
                    "availability_zone": db.get("AvailabilityZone"),
                    "multi_az": db.get("MultiAZ"),
                    "publicly_accessible": db.get("PubliclyAccessible"),
                    "creation_time": str(db.get("InstanceCreateTime")),
                })

            logger.info(f"Encontradas {len(instances)} instâncias RDS")
            return instances

        except ClientError as e:
            logger.error(f"Erro ao listar instâncias: {e}")
            raise

    def start_instance(self, instance_id: str) -> Dict:
        """Inicia uma instância RDS.

        Args:
            instance_id: ID da instância para iniciar

        Returns:
            Dicionário com resultado da operação
        """
        try:
            self.rds.start_db_instance(DBInstanceIdentifier=instance_id)
            logger.info(f"Iniciando instância RDS: {instance_id}")
            return {"status": "success", "instance_id": instance_id, "action": "started"}

        except ClientError as e:
            logger.error(f"Erro ao iniciar instância {instance_id}: {e}")
            raise

    def stop_instance(self, instance_id: str) -> Dict:
        """Para uma instância RDS.

        Args:
            instance_id: ID da instância para parar

        Returns:
            Dicionário com resultado da operação
        """
        try:
            self.rds.stop_db_instance(DBInstanceIdentifier=instance_id)
            logger.info(f"Parando instância RDS: {instance_id}")
            return {"status": "success", "instance_id": instance_id, "action": "stopped"}

        except ClientError as e:
            logger.error(f"Erro ao parar instância {instance_id}: {e}")
            raise

    def reboot_instance(self, instance_id: str) -> Dict:
        """Reinicia uma instância RDS.

        Args:
            instance_id: ID da instância para reiniciar

        Returns:
            Dicionário com resultado da operação
        """
        try:
            self.rds.reboot_db_instance(DBInstanceIdentifier=instance_id)
            logger.info(f"Reiniciando instância RDS: {instance_id}")
            return {"status": "success", "instance_id": instance_id, "action": "rebooted"}

        except ClientError as e:
            logger.error(f"Erro ao reiniciar instância {instance_id}: {e}")
            raise

    def create_snapshot(self, instance_id: str, snapshot_id: Optional[str] = None) -> Dict:
        """Cria um snapshot de uma instância RDS.

        Args:
            instance_id: ID da instância de origem
            snapshot_id: ID opcional para o snapshot

        Returns:
            Dicionário com informações do snapshot
        """
        try:
            if not snapshot_id:
                snapshot_id = f"snapshot-{instance_id}"

            response = self.rds.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_id,
                DBInstanceIdentifier=instance_id
            )

            logger.info(f"Snapshot criado: {snapshot_id}")
            return {
                "snapshot_id": response["DBSnapshot"]["DBSnapshotIdentifier"],
                "instance_id": instance_id,
                "status": response["DBSnapshot"]["Status"],
            }

        except ClientError as e:
            logger.error(f"Erro ao criar snapshot: {e}")
            raise

    def list_snapshots(self, instance_id: Optional[str] = None) -> List[Dict]:
        """Lista snapshots RDS.

        Args:
            instance_id: Filtrar por instância específica

        Returns:
            Lista de dicionários de snapshots
        """
        try:
            params = {}
            if instance_id:
                params["DBInstanceIdentifier"] = instance_id

            response = self.rds.describe_db_snapshots(**params)
            snapshots = []

            for snap in response.get("DBSnapshots", []):
                snapshots.append({
                    "snapshot_id": snap.get("DBSnapshotIdentifier"),
                    "instance_id": snap.get("DBInstanceIdentifier"),
                    "status": snap.get("Status"),
                    "engine": snap.get("Engine"),
                    "size_gb": snap.get("AllocatedStorage"),
                    "creation_time": str(snap.get("SnapshotCreateTime")),
                })

            logger.info(f"Encontrados {len(snapshots)} snapshots")
            return snapshots

        except ClientError as e:
            logger.error(f"Erro ao listar snapshots: {e}")
            raise

    def list_engine_versions(self, engine: str = "postgres") -> List[Dict]:
        """Lista versões disponíveis de um mecanismo.

        Args:
            engine: Nome do mecanismo (postgres, mysql, oracle-se, etc)

        Returns:
            Lista de versões disponíveis
        """
        try:
            response = self.rds.describe_db_engine_versions(Engine=engine)
            versions = []

            for ver in response.get("DBEngineVersions", []):
                versions.append({
                    "engine": ver.get("Engine"),
                    "engine_version": ver.get("EngineVersion"),
                    "engine_mode": ver.get("EngineMode"),
                    "default_only": ver.get("DefaultOnly"),
                })

            logger.info(f"Encontradas {len(versions)} versões de {engine}")
            return versions

        except ClientError as e:
            logger.error(f"Erro ao listar versões: {e}")
            raise