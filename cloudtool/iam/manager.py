"""Módulo de Gerenciamento IAM"""

import boto3
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IAMManager:
    """Gerencia operações IAM."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """Inicializa o Gerenciador IAM.

        Args:
            region: Região AWS (padrão: us-east-1)
            profile: Nome do perfil de credenciais AWS
        """
        self.region = region
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)
        self.iam = session.client("iam")

    def list_users(self) -> List[Dict]:
        """Lista usuários IAM.

        Returns:
            Lista de dicionários de usuários
        """
        try:
            response = self.iam.list_users()
            users = []

            for user in response.get("Users", []):
                users.append({
                    "username": user.get("UserName"),
                    "user_id": user.get("UserId"),
                    "arn": user.get("Arn"),
                    "path": user.get("Path"),
                    "created": str(user.get("CreateDate")),
                })

            logger.info(f"Encontrados {len(users)} usuários")
            return users

        except ClientError as e:
            logger.error(f"Erro ao listar usuários: {e}")
            raise

    def list_roles(self) -> List[Dict]:
        """Lista roles IAM.

        Returns:
            Lista de dicionários de roles
        """
        try:
            response = self.iam.list_roles()
            roles = []

            for role in response.get("Roles", []):
                roles.append({
                    "role_name": role.get("RoleName"),
                    "role_id": role.get("RoleId"),
                    "arn": role.get("Arn"),
                    "path": role.get("Path"),
                    "created": str(role.get("CreateDate")),
                })

            logger.info(f"Encontradas {len(roles)} roles")
            return roles

        except ClientError as e:
            logger.error(f"Erro ao listar roles: {e}")
            raise

    def list_policies(self, scope: str = "Local") -> List[Dict]:
        """Lista políticas IAM.

        Args:
            scope: Escopo (All, AWS, Local)

        Returns:
            Lista de dicionários de políticas
        """
        try:
            response = self.iam.list_policies(Scope=scope)
            policies = []

            for pol in response.get("Policies", []):
                policies.append({
                    "policy_name": pol.get("PolicyName"),
                    "policy_id": pol.get("PolicyId"),
                    "arn": pol.get("Arn"),
                    "path": pol.get("Path"),
                    "default_version": pol.get("DefaultVersionId"),
                    "attachment_count": pol.get("AttachmentCount"),
                    "created": str(pol.get("CreateDate")),
                })

            logger.info(f"Encontradas {len(policies)} políticas")
            return policies

        except ClientError as e:
            logger.error(f"Erro ao listar políticas: {e}")
            raise

    def list_groups(self) -> List[Dict]:
        """Lista grupos IAM.

        Returns:
            Lista de dicionários de grupos
        """
        try:
            response = self.iam.list_groups()
            groups = []

            for group in response.get("Groups", []):
                groups.append({
                    "group_name": group.get("GroupName"),
                    "group_id": group.get("GroupId"),
                    "arn": group.get("Arn"),
                    "path": group.get("Path"),
                    "created": str(group.get("CreateDate")),
                })

            logger.info(f"Encontrados {len(groups)} grupos")
            return groups

        except ClientError as e:
            logger.error(f"Erro ao listar grupos: {e}")
            raise

    def list_instance_profiles(self) -> List[Dict]:
        """Lista instance profiles.

        Returns:
            Lista de dicionários de instance profiles
        """
        try:
            response = self.iam.list_instance_profiles()
            profiles = []

            for profile in response.get("InstanceProfiles", []):
                profiles.append({
                    "instance_profile_name": profile.get("InstanceProfileName"),
                    "instance_profile_id": profile.get("InstanceProfileId"),
                    "arn": profile.get("Arn"),
                    "path": profile.get("Path"),
                    "created": str(profile.get("CreateDate")),
                })

            logger.info(f"Encontrados {len(profiles)} instance profiles")
            return profiles

        except ClientError as e:
            logger.error(f"Erro ao listar instance profiles: {e}")
            raise

    def get_user(self, username: str) -> Dict:
        """Obtém informações de um usuário.

        Args:
            username: Nome do usuário

        Returns:
            Dicionário com informações do usuário
        """
        try:
            response = self.iam.get_user(UserName=username)
            user = response.get("User", {})

            return {
                "username": user.get("UserName"),
                "user_id": user.get("UserId"),
                "arn": user.get("Arn"),
                "path": user.get("Path"),
                "created": str(user.get("CreateDate")),
                "password_last_used": str(user.get("PasswordLastUsed")),
            }

        except ClientError as e:
            logger.error(f"Erro ao obter usuário: {e}")
            raise

    def get_policy_version(self, policy_arn: str) -> Dict:
        """Obtém versão de uma política.

        Args:
            policy_arn: ARN da política

        Returns:
            Dicionário com a versão da política
        """
        try:
            policy_name = policy_arn.split("/")[-1]
            response = self.iam.get_policy(PolicyArn=policy_arn)
            policy = response.get("Policy", {})

            return {
                "policy_name": policy.get("PolicyName"),
                "policy_id": policy.get("PolicyId"),
                "arn": policy.get("Arn"),
                "default_version": policy.get("DefaultVersionId"),
                "attachment_count": policy.get("AttachmentCount"),
            }

        except ClientError as e:
            logger.error(f"Erro ao obter política: {e}")
            raise

    def list_access_keys(self, username: str) -> List[Dict]:
        """Lista chaves de acesso de um usuário.

        Args:
            username: Nome do usuário

        Returns:
            Lista de chaves de acesso
        """
        try:
            response = self.iam.list_access_keys(UserName=username)
            keys = []

            for key in response.get("AccessKeyMetadata", []):
                keys.append({
                    "access_key_id": key.get("AccessKeyId"),
                    "username": key.get("UserName"),
                    "status": key.get("Status"),
                    "created": str(key.get("CreateDate")),
                })

            logger.info(f"Encontradas {len(keys)} chaves de acesso")
            return keys

        except ClientError as e:
            logger.error(f"Erro ao listar chaves: {e}")
            raise

    def list_attached_user_policies(self, username: str) -> List[Dict]:
        """Lista políticas anexadas a um usuário.

        Args:
            username: Nome do usuário

        Returns:
            Lista de políticas
        """
        try:
            response = self.iam.list_attached_user_policies(UserName=username)
            policies = []

            for pol in response.get("AttachedPolicies", []):
                policies.append({
                    "policy_name": pol.get("PolicyName"),
                    "policy_arn": pol.get("PolicyArn"),
                })

            logger.info(f"Encontradas {len(policies)} políticas anexadas")
            return policies

        except ClientError as e:
            logger.error(f"Erro ao listar políticas: {e}")
            raise

    def get_account_summary(self) -> Dict:
        """Obtém resumo da conta IAM.

        Returns:
            Dicionário com resumo da conta
        """
        try:
            response = self.iam.get_account_summary()
            summary = {}

            for key, value in response.get("SummaryMap", {}).items():
                summary[key] = value

            return summary

        except ClientError as e:
            logger.error(f"Erro ao obter resumo: {e}")
            raise