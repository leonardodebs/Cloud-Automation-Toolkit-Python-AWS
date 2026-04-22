"""Módulo de Gerenciamento ECR"""

import boto3
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ECRManager:
    """Gerencia operações ECR."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """Inicializa o Gerenciador ECR.

        Args:
            region: Região AWS (padrão: us-east-1)
            profile: Nome do perfil de credenciais AWS
        """
        self.region = region
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)
        self.ecr = session.client("ecr")

    def list_repositories(self) -> List[Dict]:
        """Lista repositórios ECR.

        Returns:
            Lista de dicionários de repositórios
        """
        try:
            response = self.ecr.describe_repositories()
            repos = []

            for repo in response.get("repositories", []):
                repos.append({
                    "name": repo.get("repositoryName"),
                    "arn": repo.get("repositoryArn"),
                    "uri": repo.get("repositoryUri"),
                    "registry_id": repo.get("registryId"),
                    "created": str(repo.get("createdAt")),
                })

            logger.info(f"Encontrados {len(repos)} repositórios")
            return repos

        except ClientError as e:
            logger.error(f"Erro ao listar repositórios: {e}")
            raise

    def list_images(
        self,
        repository: str,
        max_results: int = 100,
    ) -> List[Dict]:
        """Lista imagens em um repositório.

        Args:
            repository: Nome do repositório
            max_results: Número máximo de resultados

        Returns:
            Lista de dicionários de imagens
        """
        try:
            response = self.ecr.list_images(
                repositoryName=repository,
                maxResults=max_results,
            )
            images = []

            for image in response.get("imageIds", []):
                images.append({
                    "registry": image.get("registryId"),
                    "repository": repository,
                    "digest": image.get("imageDigest"),
                    "tags": image.get("imageTags", []),
                })

            logger.info(f"Encontradas {len(images)} imagens")
            return images

        except ClientError as e:
            logger.error(f"Erro ao listar imagens: {e}")
            raise

    def describe_images(
        self,
        repository: str,
        image_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Describe imagens em detalhes.

        Args:
            repository: Nome do repositório
            image_ids: Lista de image digests ou tags

        Returns:
            Lista de detalhes de imagens
        """
        try:
            params: Dict = {"repositoryName": repository}
            if image_ids:
                image_id_list = [{"imageDigest": img} for img in image_ids]
                params["imageIds"] = image_id_list

            response = self.ecr.describe_images(**params)
            images: List[Dict] = []

            for image in response.get("imageDetails", []):
                images.append({
                    "registry": image.get("registryId"),
                    "repository": repository,
                    "digest": image.get("imageDigest"),
                    "tags": image.get("imageTags", []),
                    "size": image.get("imageSizeInBytes"),
                    "created": str(image.get("imagePushedAt")),
                    "last_scan": str(image.get("lastImageScanTimestamp")),
                    "scan_status": image.get("imageScanStatus", {}).get("status"),
                })

            logger.info(f"Encontradas {len(images)} imagens")
            return images

        except ClientError as e:
            logger.error(f"Erro ao descrever imagens: {e}")
            raise

    def get_repository_policy(self, repository: str) -> Dict:
        """Obtém política de um repositório.

        Args:
            repository: Nome do repositório

        Returns:
            Dicionário com política
        """
        try:
            response = self.ecr.get_repository_policy(repositoryName=repository)
            policy = response.get("policyText", {})

            return {
                "registry": repository,
                "policy": policy,
            }

        except ClientError as e:
            logger.error(f"Erro ao obter política: {e}")
            raise

    def describe_pull_through_cache_rules(self) -> List[Dict]:
        """Lista regras de pull through cache.

        Returns:
            Lista de regras
        """
        try:
            response = self.ecr.describe_pull_through_cache_rules()
            rules = []

            for rule in response.get("pullThroughCacheRules", []):
                rules.append({
                    "upstream_registry_url": rule.get("upstreamRegistryUrl"),
                    "repository_prefix": rule.get("repositoryPrefix"),
                    "registry": rule.get("registryId"),
                })

            logger.info(f"Encontradas {len(rules)} regras")
            return rules

        except ClientError as e:
            logger.error(f"Erro ao listar regras: {e}")
            raise

    def get_authorization_token(self) -> Dict:
        """Obtém token de autorização ECR.

        Returns:
            Dicionário com token (Base64)
        """
        try:
            response = self.ecr.get_authorization_token()
            auth = response.get("authorizationData", [])[0]

            return {
                "username": auth.get("username"),
                "password": auth.get("password"),
                "endpoint": auth.get("proxyEndpoint"),
            }

        except ClientError as e:
            logger.error(f"Erro ao obter token: {e}")
            raise

    def list_tags_for_resource(self, repository: str) -> List[Dict]:
        """Lista tags de um repositório.

        Args:
            repository: Nome do repositório

        Returns:
            Lista de tags
        """
        try:
            response = self.ecr.list_tags_for_resource(resourceArn=self._get_repo_arn(repository))
            tags = []

            for tag in response.get("tags", []):
                tags.append({
                    "key": tag.get("Key"),
                    "value": tag.get("Value"),
                })

            logger.info(f"Encontradas {len(tags)} tags")
            return tags

        except ClientError as e:
            logger.error(f"Erro ao listar tags: {e}")
            raise

    def _get_repo_arn(self, repository: str) -> str:
        """Obtém ARN de um repositório."""
        response = self.ecr.describe_repositories(repositoryNames=[repository])
        return response["repositories"][0]["repositoryArn"]