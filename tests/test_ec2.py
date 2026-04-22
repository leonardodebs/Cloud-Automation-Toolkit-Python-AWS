import pytest
from unittest.mock import patch, MagicMock, call


class TestEC2Manager:
    """Testes para EC2Manager."""

    def test_list_instances_empty(self, mock_aws_session):
        """Testa listagem com nenhuma instância."""
        from cloudtool.ec2.manager import EC2Manager
        
        mock_aws_session.describe_instances.return_value = {"Reservations": []}
        manager = EC2Manager(region="us-east-1")
        
        result = manager.list_instances()
        
        assert result == []
        mock_aws_session.describe_instances.assert_called_once()

    def test_list_instances_with_data(self, mock_aws_session):
        """Testa listagem com instâncias."""
        from cloudtool.ec2.manager import EC2Manager
        
        mock_aws_session.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-1234567890abcdef0",
                    "InstanceType": "t3.micro",
                    "State": {"Name": "running"},
                    "PublicIpAddress": "1.2.3.4",
                    "PrivateIpAddress": "10.0.0.10",
                    "ImageId": "ami-12345678",
                    "LaunchTime": "2024-01-01T00:00:00Z",
                    "Placement": {"AvailabilityZone": "us-east-1a"},
                    "Tags": [{"Key": "Name", "Value": "web-server"}]
                }]
            }]
        }
        
        manager = EC2Manager(region="us-east-1")
        result = manager.list_instances()
        
        assert len(result) == 1
        assert result[0]["instance_id"] == "i-1234567890abcdef0"
        assert result[0]["instance_type"] == "t3.micro"
        assert result[0]["state"] == "running"
        assert result[0]["name"] == "web-server"

    def test_list_instances_filter_running(self, mock_aws_session):
        """Testa listagem filtrando por estado."""
        from cloudtool.ec2.manager import EC2Manager
        
        manager = EC2Manager(region="us-east-1")
        manager.list_instances(state_filter="running")
        
        mock_aws_session.describe_instances.assert_called_once()
        call_args = mock_aws_session.describe_instances.call_args
        assert call_args[1]["Filters"][0]["Values"] == ["16"]

    def test_start_instance(self, mock_aws_session):
        """Testa iniciar instância."""
        from cloudtool.ec2.manager import EC2Manager
        
        manager = EC2Manager(region="us-east-1")
        result = manager.start_instance("i-1234567890abcdef0")
        
        assert result["status"] == "success"
        assert result["instance_id"] == "i-1234567890abcdef0"
        assert result["action"] == "started"
        mock_aws_session.start_instances.assert_called_once_with(InstanceIds=["i-1234567890abcdef0"])

    def test_stop_instance(self, mock_aws_session):
        """Testa parar instância."""
        from cloudtool.ec2.manager import EC2Manager
        
        manager = EC2Manager(region="us-east-1")
        result = manager.stop_instance("i-1234567890abcdef0")
        
        assert result["status"] == "success"
        assert result["action"] == "stopped"
        mock_aws_session.stop_instances.assert_called_once_with(InstanceIds=["i-1234567890abcdef0"], Force=False)

    def test_stop_instance_force(self, mock_aws_session):
        """Testa forçar parada."""
        from cloudtool.ec2.manager import EC2Manager
        
        manager = EC2Manager(region="us-east-1")
        result = manager.stop_instance("i-1234567890abcdef0", force=True)
        
        mock_aws_session.stop_instances.assert_called_once_with(InstanceIds=["i-1234567890abcdef0"], Force=True)

    def test_create_snapshot(self, mock_aws_session):
        """Testa criar snapshot."""
        from cloudtool.ec2.manager import EC2Manager
        
        mock_aws_session.create_snapshot.return_value = {
            "SnapshotId": "snap-1234567890abcdef0",
            "VolumeId": "vol-1234567890abcdef0",
            "State": "pending"
        }
        
        manager = EC2Manager(region="us-east-1")
        result = manager.create_snapshot("vol-1234567890abcdef0", "Meu snapshot")
        
        assert result["snapshot_id"] == "snap-1234567890abcdef0"
        assert result["volume_id"] == "vol-1234567890abcdef0"

    def test_list_volumes(self, mock_aws_session):
        """Testa listar volumes."""
        from cloudtool.ec2.manager import EC2Manager
        
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
        
        manager = EC2Manager(region="us-east-1")
        result = manager.list_volumes()
        
        assert len(result) == 1
        assert result[0]["volume_id"] == "vol-1234567890abcdef0"
        assert result[0]["size"] == 100
        assert result[0]["volume_type"] == "gp3"

    def test_get_instance_details(self, mock_aws_session):
        """Testa obter detalhes de instância."""
        from cloudtool.ec2.manager import EC2Manager
        
        mock_aws_session.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-1234567890abcdef0",
                    "InstanceType": "t3.micro",
                    "State": {"Name": "running"},
                    "PublicIpAddress": "1.2.3.4",
                    "PrivateIpAddress": "10.0.0.10",
                    "ImageId": "ami-12345678",
                    "LaunchTime": "2024-01-01T00:00:00Z",
                    "Placement": {"AvailabilityZone": "us-east-1a"},
                    "VpcId": "vpc-12345678",
                    "SubnetId": "subnet-12345678",
                    "SecurityGroups": [{"GroupName": "sg-web", "GroupId": "sg-12345678"}],
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "Tags": [{"Key": "Name", "Value": "web-server"}]
                }]
            }]
        }
        
        manager = EC2Manager(region="us-east-1")
        result = manager.get_instance_details("i-1234567890abcdef0")
        
        assert result["instance_id"] == "i-1234567890abcdef0"
        assert result["vpc_id"] == "vpc-12345678"
        assert result["subnet_id"] == "subnet-12345678"

    def test_get_instance_not_found(self, mock_aws_session):
        """Testa instância não encontrada."""
        from cloudtool.ec2.manager import EC2Manager
        
        mock_aws_session.describe_instances.return_value = {"Reservations": []}
        
        manager = EC2Manager(region="us-east-1")
        
        with pytest.raises(ValueError, match="não encontrada"):
            manager.get_instance_details("i-inexistente")