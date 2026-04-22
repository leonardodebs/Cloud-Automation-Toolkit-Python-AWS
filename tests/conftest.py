import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_aws_session():
    """Cria sessão mockada para testes."""
    with patch('cloudtool.ec2.manager.boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_session.return_value.resource.return_value = mock_client
        yield mock_client


@pytest.fixture
def ec2_manager(mock_aws_session):
    """Cria EC2Manager com AWS mockada."""
    from cloudtool.ec2.manager import EC2Manager
    return EC2Manager(region="us-east-1")


@pytest.fixture
def s3_manager(mock_aws_session):
    """Cria S3Manager com AWS mockada."""
    from cloudtool.s3.manager import S3Manager
    return S3Manager(region="us-east-1")


@pytest.fixture
def report_generator(mock_aws_session):
    """Cria ReportGenerator com AWS mockada."""
    from cloudtool.reports.generator import ReportGenerator
    return ReportGenerator(region="us-east-1")