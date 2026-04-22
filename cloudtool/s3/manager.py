"""Módulo de Gerenciamento de Buckets S3"""

import boto3
import os
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Manager:
    """Gerencia operações S3 para tarefas comuns."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """Inicializa o Gerenciador S3.

        Args:
            region: Região AWS (padrão: us-east-1)
            profile: Nome do perfil de credenciais AWS
        """
        self.region = region
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)
        self.s3 = session.client("s3")
        self.s3_resource = session.resource("s3")

    def list_buckets(self) -> List[Dict]:
        """Lista todos os buckets S3.

        Returns:
            Lista de dicionários de buckets com metadados
        """
        try:
            response = self.s3.list_buckets()
            buckets = []

            for bucket in response.get("Buckets", []):
                bucket_name = bucket.get("Name")
                try:
                    location = self.s3.get_bucket_location(Bucket=bucket_name)
                    region = location.get("LocationConstraint") or "us-east-1"

                    tags_response = self.s3.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("Tags", [])}
                except ClientError:
                    region = "desconhecido"
                    tags = {}

                buckets.append({
                    "name": bucket_name,
                    "creation_date": str(bucket.get("CreationDate")),
                    "region": region,
                    "tags": tags,
                })

            logger.info(f"Encontrados {len(buckets)} buckets")
            return buckets

        except ClientError as e:
            logger.error(f"Erro ao listar buckets: {e}")
            raise

    def upload_file(self, file_path: str, bucket: str, key: Optional[str] = None) -> Dict:
        """Faz upload de um arquivo para o S3.

        Args:
            file_path: Caminho do arquivo local
            bucket: Nome do bucket de destino
            key: Chave do objeto S3 (padrão: nome do arquivo)

        Returns:
            Dicionário com resultado do upload
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            if not key:
                key = os.path.basename(file_path)

            file_size = os.path.getsize(file_path)

            self.s3.upload_file(file_path, bucket, key)
            logger.info(f"Upload realizado: {file_path} para s3://{bucket}/{key}")

            return {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "size": file_size,
                "file_path": file_path,
            }

        except (ClientError, FileNotFoundError) as e:
            logger.error(f"Erro ao fazer upload do arquivo: {e}")
            raise

    def download_file(self, bucket: str, key: str, destination: str) -> Dict:
        """Baixa um arquivo do S3.

        Args:
            bucket: Nome do bucket de origem
            key: Chave do objeto S3
            destination: Caminho de destino local

        Returns:
            Dicionário com resultado do download
        """
        try:
            self.s3.download_file(bucket, key, destination)
            logger.info(f"Download realizado: s3://{bucket}/{key} para {destination}")

            return {
                "status": "success",
                "bucket": bucket,
                "key": key,
                "destination": destination,
            }

        except ClientError as e:
            logger.error(f"Erro ao baixar arquivo: {e}")
            raise

    def sync_directory(self, local_dir: str, bucket: str, prefix: str = "") -> Dict:
        """Sincroniza um diretório local com bucket S3.

        Args:
            local_dir: Caminho do diretório local
            bucket: Nome do bucket de destino
            prefix: Prefixo/chave do S3

        Returns:
            Dicionário com resultados da sincronização
        """
        try:
            if not os.path.isdir(local_dir):
                raise NotADirectoryError(f"Diretório não encontrado: {local_dir}")

            local_path = Path(local_dir)
            uploaded = []
            skipped = []
            errors = []

            for file_path in local_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(local_path)
                    s3_key = f"{prefix}/{relative_path}" if prefix else str(relative_path)

                    try:
                        if self._should_upload(bucket, s3_key, file_path):
                            self.s3.upload_file(str(file_path), bucket, s3_key)
                            uploaded.append(s3_key)
                            logger.info(f"Upload realizado: {s3_key}")
                        else:
                            skipped.append(s3_key)

                    except ClientError as e:
                        errors.append({"key": s3_key, "error": str(e)})

            result = {
                "status": "success",
                "bucket": bucket,
                "local_dir": local_dir,
                "uploaded": len(uploaded),
                "skipped": len(skipped),
                "errors": len(errors),
            }

            if uploaded:
                result["uploaded_files"] = uploaded
            if errors:
                result["error_details"] = errors

            logger.info(f"Sincronizado {local_dir} para s3://{bucket}: {len(uploaded)} uploads, {len(skipped)} ignorados")
            return result

        except (ClientError, NotADirectoryError) as e:
            logger.error(f"Erro ao sincronizar diretório: {e}")
            raise

    def _should_upload(self, bucket: str, key: str, file_path: Path) -> bool:
        """Verifica se o arquivo deve ser fazer upload (compara ETags)."""
        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)
            s3_etag = response.get("ETag", "").strip('"')

            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
            local_etag = md5_hash.hexdigest()

            return s3_etag != local_etag
        except ClientError:
            return True

    def list_objects(self, bucket: str, prefix: str = "") -> List[Dict]:
        """Lista objetos em um bucket.

        Args:
            bucket: Nome do bucket
            prefix: Filtro de prefixo da chave do objeto

        Returns:
            Lista de dicionários de objetos
        """
        try:
            params = {"Bucket": bucket}
            if prefix:
                params["Prefix"] = prefix

            response = self.s3.list_objects_v2(**params)
            objects = []

            for obj in response.get("Contents", []):
                objects.append({
                    "key": obj.get("Key"),
                    "size": obj.get("Size"),
                    "last_modified": str(obj.get("LastModified")),
                    "etag": obj.get("ETag"),
                    "storage_class": obj.get("StorageClass"),
                })

            logger.info(f"Encontrados {len(objects)} objetos em {bucket}")
            return objects

        except ClientError as e:
            logger.error(f"Erro ao listar objetos: {e}")
            raise

    def clean_old_objects(self, bucket: str, days: int = 30, prefix: str = "") -> Dict:
        """Exclui objetos mais antigos que o número de dias especificado.

        Args:
            bucket: Nome do bucket
            days: Excluir objetos mais antigos que este número de dias
            prefix: Excluir apenas objetos com este prefixo

        Returns:
            Dicionário com resultados da exclusão
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted = []
            errors = []

            objects = self.list_objects(bucket, prefix)

            for obj in objects:
                last_modified = obj["last_modified"]
                if isinstance(last_modified, str):
                    last_modified = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))

                if last_modified.replace(tzinfo=None) < cutoff_date:
                    try:
                        self.s3.delete_object(Bucket=bucket, Key=obj["key"])
                        deleted.append(obj["key"])
                        logger.info(f"Excluído: {obj['key']}")
                    except ClientError as e:
                        errors.append({"key": obj["key"], "error": str(e)})

            result = {
                "status": "success",
                "bucket": bucket,
                "days_threshold": days,
                "deleted": len(deleted),
                "errors": len(errors),
            }

            if deleted:
                result["deleted_objects"] = deleted
            if errors:
                result["error_details"] = errors

            logger.error(f"Limpeza em {bucket}: excluídos {len(deleted)} objetos mais antigos que {days} dias")
            return result

        except ClientError as e:
            logger.error(f"Erro ao limpar objetos: {e}")
            raise

    def get_bucket_size(self, bucket: str) -> Dict:
        """Obtém o tamanho total dos objetos em um bucket.

        Args:
            bucket: Nome do bucket

        Returns:
            Dicionário com informações de tamanho do bucket
        """
        try:
            objects = self.list_objects(bucket)
            total_size = sum(obj["size"] for obj in objects)
            object_count = len(objects)

            return {
                "bucket": bucket,
                "total_size_bytes": total_size,
                "total_size_gb": round(total_size / (1024**3), 2),
                "object_count": object_count,
            }

        except ClientError as e:
            logger.error(f"Erro ao obter tamanho do bucket: {e}")
            raise
