import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestReportGenerator:
    """Testes para ReportGenerator."""

    def test_generate_running_instances_report(self, mock_aws_session):
        """Testa relatório de instâncias em execução."""
        from cloudtool.reports.generator import ReportGenerator
        
        mock_aws_session.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-1234567890abcdef0",
                    "InstanceType": "t3.micro",
                    "State": {"Name": "running"},
                    "PublicIpAddress": "1.2.3.4",
                    "PrivateIpAddress": "10.0.0.10",
                    "Placement": {"AvailabilityZone": "us-east-1a"},
                    "LaunchTime": "2024-01-01T00:00:00Z",
                    "Tags": [{"Key": "Name", "Value": "web-server"}]
                }]
            }]
        }
        
        generator = ReportGenerator(region="us-east-1")
        result = generator.generate_running_instances_report()
        
        assert result["report_type"] == "running_instances"
        assert result["total_instances"] == 1
        assert result["total_vcpus"] == 2
        assert result["total_memory_gb"] == 1

    def test_generate_running_instances_empty(self, mock_aws_session):
        """Testa relatório vazio."""
        from cloudtool.reports.generator import ReportGenerator
        
        mock_aws_session.describe_instances.return_value = {"Reservations": []}
        
        generator = ReportGenerator(region="us-east-1")
        result = generator.generate_running_instances_report()
        
        assert result["total_instances"] == 0
        assert result["total_vcpus"] == 0

    def test_generate_storage_report(self, mock_aws_session):
        """Testa relatório de armazenamento."""
        from cloudtool.reports.generator import ReportGenerator
        
        mock_aws_session.describe_volumes.return_value = {
            "Volumes": [{
                "VolumeId": "vol-1234567890abcdef0",
                "Size": 100,
                "VolumeType": "gp3",
                "State": "available",
                "AvailabilityZone": "us-east-1a",
                "Encrypted": True
            }]
        }
        mock_aws_session.describe_snapshots.return_value = {
            "Snapshots": [{
                "SnapshotId": "snap-1234567890abcdef0",
                "VolumeSize": 50,
                "State": "completed",
                "Description": "Test snapshot"
            }]
        }
        mock_aws_session.list_buckets.return_value = {
            "Buckets": [{"Name": "meu-bucket", "CreationDate": "2024-01-01T00:00:00Z"}]
        }
        
        generator = ReportGenerator(region="us-east-1")
        result = generator.generate_storage_report()
        
        assert result["report_type"] == "storage_usage"
        assert result["ebs_volumes"]["count"] == 1
        assert result["ebs_volumes"]["total_size_gb"] == 100
        assert result["ebs_snapshots"]["count"] == 1
        assert result["s3_buckets"]["count"] == 1

    def test_generate_cost_estimation_report(self, mock_aws_session):
        """Testa estimativa de custos."""
        from cloudtool.reports.generator import ReportGenerator
        
        mock_aws_session.get_cost_and_usage.return_value = {
            "ResultsByTime": [{
                "Groups": [{
                    "Keys": ["Amazon EC2"],
                    "Metrics": {"UnblendedCost": {"Amount": "100.00"}}
                }]
            }]
        }
        
        generator = ReportGenerator(region="us-east-1")
        result = generator.generate_cost_estimation_report(days=30)
        
        assert result["report_type"] == "cost_estimation"
        assert result["total_cost"] == 100.0
        assert result["currency"] == "USD"
        assert result["daily_average"] == 3.33

    def test_generate_cost_estimation_no_data(self, mock_aws_session):
        """Testa estimativa sem dados."""
        from cloudtool.reports.generator import ReportGenerator
        
        mock_aws_session.get_cost_and_usage.return_value = {"ResultsByTime": []}
        
        generator = ReportGenerator(region="us-east-1")
        result = generator.generate_cost_estimation_report(days=30)
        
        assert result["total_cost"] == 0.0
        assert result["daily_average"] == 0.0

    def test_generate_full_report(self, mock_aws_session):
        """Testa relatório completo."""
        from cloudtool.reports.generator import ReportGenerator
        
        mock_aws_session.describe_instances.return_value = {"Reservations": []}
        mock_aws_session.describe_volumes.return_value = {"Volumes": []}
        mock_aws_session.describe_snapshots.return_value = {"Snapshots": []}
        mock_aws_session.list_buckets.return_value = {"Buckets": []}
        mock_aws_session.get_cost_and_usage.return_value = {"ResultsByTime": []}
        
        generator = ReportGenerator(region="us-east-1")
        result = generator.generate_full_report()
        
        assert "full_report" in result
        assert "running_instances" in result["full_report"]
        assert "storage" in result["full_report"]
        assert "cost" in result["full_report"]


class TestInstanceSpecs:
    """Testes para especificações de tipo de instância."""

    def test_t2_instances(self, report_generator):
        """Testa instâncias T2."""
        from cloudtool.reports.generator import ReportGenerator
        
        result = ReportGenerator._get_instance_type_specs(ReportGenerator, "t2.micro")
        assert result == (1, 1)

    def test_t3_instances(self, report_generator):
        """Testa instâncias T3."""
        from cloudtool.reports.generator import ReportGenerator
        
        result = ReportGenerator._get_instance_type_specs(ReportGenerator, "t3.large")
        assert result == (2, 8)

    def test_m5_instances(self, report_generator):
        """Testa instâncias M5."""
        from cloudtool.reports.generator import ReportGenerator
        
        result = ReportGenerator._get_instance_type_specs(ReportGenerator, "m5.2xlarge")
        assert result == (8, 32)

    def test_c5_instances(self, report_generator):
        """Testa instâncias C5."""
        from cloudtool.reports.generator import ReportGenerator
        
        result = ReportGenerator._get_instance_type_specs(ReportGenerator, "c5.4xlarge")
        assert result == (16, 32)

    def test_r5_instances(self, report_generator):
        """Testa instâncias R5."""
        from cloudtool.reports.generator import ReportGenerator
        
        result = ReportGenerator._get_instance_type_specs(ReportGenerator, "r5.4xlarge")
        assert result == (16, 128)

    def test_unknown_instance_type(self, report_generator):
        """Testa tipo desconhecido."""
        from cloudtool.reports.generator import ReportGenerator
        
        result = ReportGenerator._get_instance_type_specs(ReportGenerator, "t-something.new")
        assert result == (None, None)