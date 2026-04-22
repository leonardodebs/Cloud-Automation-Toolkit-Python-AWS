"""Módulo de Gerenciamento CloudWatch"""

import boto3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudWatchManager:
    """Gerencia operações CloudWatch."""

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """Inicializa o Gerenciador CloudWatch.

        Args:
            region: Região AWS (padrão: us-east-1)
            profile: Nome do perfil de credenciais AWS
        """
        self.region = region
        if profile:
            session = boto3.Session(profile_name=profile, region_name=region)
        else:
            session = boto3.Session(region_name=region)
        self.cw = session.client("cloudwatch")
        self.logs = session.client("logs")

    def list_alarms(self, state_filter: Optional[str] = None) -> List[Dict]:
        """Lista alarmes CloudWatch.

        Args:
            state_filter: Filtrar por estado (OK, ALARM, INSUFFICIENT_DATA)

        Returns:
            Lista de dicionários de alarmes
        """
        try:
            params = {}
            if state_filter:
                params["StateValue"] = state_filter

            response = self.cw.describe_alarms(**params)
            alarms = []

            for alarm in response.get("MetricAlarms", []):
                alarms.append({
                    "alarm_name": alarm.get("AlarmName"),
                    "alarm_arn": alarm.get("AlarmArn"),
                    "state": alarm.get("StateValue"),
                    "state_reason": alarm.get("StateReason"),
                    "metric_name": alarm.get("MetricName"),
                    "namespace": alarm.get("Namespace"),
                    "statistic": alarm.get("Statistic"),
                    "period": alarm.get("Period"),
                    "evaluation_periods": alarm.get("EvaluationPeriods"),
                    "threshold": alarm.get("Threshold"),
                    "comparison": alarm.get("ComparisonOperator"),
                    "actions_enabled": alarm.get("ActionsEnabled"),
                    "alarm_actions": alarm.get("AlarmActions", []),
                })

            logger.info(f"Encontrados {len(alarms)} alarmes")
            return alarms

        except ClientError as e:
            logger.error(f"Erro ao listar alarmes: {e}")
            raise

    def get_metric_statistics(
        self,
        namespace: str,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        period: int = 300,
        statistic: str = "Average",
    ) -> List[Dict]:
        """Obtém estatísticas de uma métrica.

        Args:
            namespace: Namespace da métrica (AWS/EC2, AWS/RDS, etc)
            metric_name: Nome da métrica
            start_time: Tempo inicial
            end_time: Tempo final
            period: Período em segundos
            statistic: Estatística (Average, Sum, Maximum, Minimum)

        Returns:
            Lista de pontos de dados
        """
        try:
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(hours=1)

            response = self.cw.get_metric_statistics(
                Namespace=namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=[statistic],
            )

            data_points = []
            for point in response.get("Datapoints", []):
                data_points.append({
                    "timestamp": str(point.get("Timestamp")),
                    "average": point.get("Average"),
                    "minimum": point.get("Minimum"),
                    "maximum": point.get("Maximum"),
                    "sum": point.get("Sum"),
                    "sample_count": point.get("SampleCount"),
                })

            logger.info(f"Encontrados {len(data_points)} pontos")
            return data_points

        except ClientError as e:
            logger.error(f"Erro ao obter métricas: {e}")
            raise

    def list_metrics(self, namespace: Optional[str] = None) -> List[Dict]:
        """Lista métricas disponíveis.

        Args:
            namespace: Filtrar por namespace

        Returns:
            Lista de métricas
        """
        try:
            params = {}
            if namespace:
                params["Namespace"] = namespace

            response = self.cw.list_metrics(**params)
            metrics = []

            for metric in response.get("Metrics", []):
                metrics.append({
                    "namespace": metric.get("Namespace"),
                    "metric_name": metric.get("MetricName"),
                    "dimensions": metric.get("Dimensions", []),
                })

            logger.info(f"Encontradas {len(metrics)} métricas")
            return metrics

        except ClientError as e:
            logger.error(f"Erro ao listar métricas: {e}")
            raise

    def put_metric_data(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str = "Count",
    ) -> Dict:
        """Publica dados de métrica customizada.

        Args:
            namespace: Namespace da métrica
            metric_name: Nome da métrica
            value: Valor da métrica
            unit: Unidade (Count, Bytes, etc)

        Returns:
            Dicionário com resultado
        """
        try:
            self.cw.put_metric_data(
                Namespace=namespace,
                MetricData=[{
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": unit,
                }]
            )

            logger.info(f"Métrica publicada: {namespace}/{metric_name}")
            return {"status": "success", "namespace": namespace, "metric_name": metric_name}

        except ClientError as e:
            logger.error(f"Erro ao publicar métrica: {e}")
            raise

    def describe_alarm_history(
        self,
        alarm_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """Describe histórico de alarmes.

        Args:
            alarm_name: Nome do alarme
            start_time: Tempo inicial

        Returns:
            Lista de entradas de histórico
        """
        try:
            params = {}
            if alarm_name:
                params["AlarmName"] = alarm_name
            if start_time:
                params["StartTime"] = start_time

            response = self.cw.describe_alarm_history(**params)
            history = []

            for entry in response.get("AlarmHistoryItems", []):
                history.append({
                    "alarm_name": entry.get("AlarmName"),
                    "timestamp": str(entry.get("Timestamp")),
                    "action": entry.get("HistoryData"),
                    "history_type": entry.get("HistoryType"),
                })

            logger.info(f"Encontradas {len(history)} entradas")
            return history

        except ClientError as e:
            logger.error(f"Erro ao obter histórico: {e}")
            raise

    def list_log_groups(self) -> List[Dict]:
        """Lista grupos de logs.

        Returns:
            Lista de grupos de logs
        """
        try:
            response = self.logs.describe_log_groups()
            groups = []

            for group in response.get("logGroups", []):
                groups.append({
                    "arn": group.get("arn"),
                    "name": group.get("logGroupName"),
                    "creation_time": group.get("creationTime"),
                    "retention_days": group.get("retentionInDays"),
                    "storage_size": group.get("storedBytes"),
                })

            logger.info(f"Encontrados {len(groups)} grupos de logs")
            return groups

        except ClientError as e:
            logger.error(f"Erro ao listar grupos: {e}")
            raise

    def get_log_events(
        self,
        log_group: str,
        limit: int = 100,
        start_time: Optional[int] = None,
    ) -> List[Dict]:
        """Obtém eventos de um grupo de logs.

        Args:
            log_group: Nome do grupo de logs
            limit: Número máximo de eventos
            start_time: Timestamp inicial

        Returns:
            Lista de eventos
        """
        try:
            params = {
                "logGroupName": log_group,
                "Limit": limit,
            }
            if start_time:
                params["startTime"] = start_time

            response = self.logs.get_log_events(**params)
            events = []

            for event in response.get("events", []):
                events.append({
                    "timestamp": event.get("timestamp"),
                    "message": event.get("message"),
                    "ingestion_time": event.get("ingestionTime"),
                })

            logger.info(f"Encontrados {len(events)} eventos")
            return events

        except ClientError as e:
            logger.error(f"Erro ao obter eventos: {e}")
            raise

    def filter_log_events(
        self,
        log_group: str,
        filter_pattern: str,
        start_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """Filtra eventos de logs por padrão.

        Args:
            log_group: Nome do grupo de logs
            filter_pattern: Padrão de filtro (ex: "ERROR | WARN")
            start_time: Tempo inicial

        Returns:
            Lista de eventos filtrados
        """
        try:
            params = {
                "logGroupName": log_group,
                "filterPattern": filter_pattern,
            }
            if start_time:
                params["startTime"] = start_time

            response = self.logs.filter_log_events(**params)
            events = []

            for event in response.get("events", []):
                events.append({
                    "timestamp": event.get("timestamp"),
                    "message": event.get("message"),
                    "ingestion_time": event.get("ingestionTime"),
                })

            logger.info(f"Encontrados {len(events)} eventos")
            return events

        except ClientError as e:
            logger.error(f"Erro ao filtrar eventos: {e}")
            raise