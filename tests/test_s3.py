import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestS3Manager:
    """Testes para S3Manager."""

    def test_list_buckets(self, mock_aws_session):
        """Testa listar buckets."""
        from cloudtool.s3.manager import S3Manager
        
        mock_aws_session.list_buckets.return_value = {
            "Buckets": [{"Name": "meu-bucket", "CreationDate": "2024-01-01T00:00:00Z"}]
        }
        mock_aws_session.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}
        mock_aws_session.get_bucket_tagging.return_value = {"Tags": [{"Key": "env", "Value": "prod"}]}
        
        manager = S3Manager(region="us-east-1")
        result = manager.list_buckets()
        
        assert len(result) == 1
        assert result[0]["name"] == "meu-bucket"
        assert result[0]["region"] == "us-east-1"
        assert result[0]["tags"] == {"env": "prod"}

    def test_upload_file_not_found(self, mock_aws_session):
        """Testa upload com arquivo inexistente."""
        from cloudtool.s3.manager import S3Manager
        
        manager = S3Manager(region="us-east-1")
        
        with pytest.raises(FileNotFoundError):
            manager.upload_file("/caminho/inexistente.txt", "meu-bucket")

    @patch('cloudtool.s3.manager.os.path.exists', return_value=True)
    @patch('cloudtool.s3.manager.os.path.getsize', return_value=1024)
    def test_upload_file(self, mock_size, mock_exists, mock_aws_session):
        """Testa upload de arquivo."""
        from cloudtool.s3.manager import S3Manager
        
        manager = S3Manager(region="us-east-1")
        result = manager.upload_file("arquivo.txt", "meu-bucket")
        
        assert result["status"] == "success"
        assert result["bucket"] == "meu-bucket"
        assert result["size"] == 1024
        mock_aws_session.upload_file.assert_called_once()

    @patch('cloudtool.s3.manager.os.path.exists', return_value=True)
    @patch('cloudtool.s3.manager.os.path.getsize', return_value=1024)
    def test_upload_file_with_key(self, mock_size, mock_exists, mock_aws_session):
        """Testa upload com chave personalizada."""
        from cloudtool.s3.manager import S3Manager
        
        manager = S3Manager(region="us-east-1")
        result = manager.upload_file("arquivo.txt", "meu-bucket", "prefixo/arquivo.txt")
        
        mock_aws_session.upload_file.assert_called_with("arquivo.txt", "meu-bucket", "prefixo/arquivo.txt")

    def test_download_file(self, mock_aws_session):
        """Testa download de arquivo."""
        from cloudtool.s3.manager import S3Manager
        
        manager = S3Manager(region="us-east-1")
        result = manager.download_file("meu-bucket", "chave/arquivo.txt", "local.txt")
        
        assert result["status"] == "success"
        assert result["bucket"] == "meu-bucket"
        assert result["key"] == "chave/arquivo.txt"
        mock_aws_session.download_file.assert_called_with("meu-bucket", "chave/arquivo.txt", "local.txt")

    def test_sync_directory_not_found(self, mock_aws_session):
        """Testa sync com diretório inexistente."""
        from cloudtool.s3.manager import S3Manager
        
        manager = S3Manager(region="us-east-1")
        
        with patch('cloudtool.s3.manager.os.path.isdir', return_value=False):
            with pytest.raises(NotADirectoryError):
                manager.sync_directory("/dir/inexistente", "meu-bucket")

    @patch('cloudtool.s3.manager.Path')
    @patch('cloudtool.s3.manager.os.path.isdir', return_value=True)
    def test_sync_directory(self, mock_isdir, mock_path, mock_aws_session):
        """Testa sincronização de diretório."""
        from cloudtool.s3.manager import S3Manager
        from botocore.exceptions import ClientError
        from pathlib import Path
        import types
        
        mock_file = MagicMock()
        mock_file.is_file.return_value = True
        mock_file.relative_to.return_value = Path("arquivo.txt")
        
        mock_iter = MagicMock()
        mock_iter.rglob.return_value = [mock_file]
        mock_path.return_value = mock_iter
        
        error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        mock_aws_session.head_object.side_effect = ClientError(error_response, "HeadObject")
        
        manager = S3Manager(region="us-east-1")
        result = manager.sync_directory("./dir", "meu-bucket")
        
        assert result["status"] == "success"
        assert result["bucket"] == "meu-bucket"

    def test_list_objects(self, mock_aws_session):
        """Testa listar objetos."""
        from cloudtool.s3.manager import S3Manager
        
        mock_aws_session.list_objects_v2.return_value = {
            "Contents": [{
                "Key": "chave/arquivo.txt",
                "Size": 1024,
                "LastModified": "2024-01-01T00:00:00Z",
                "ETag": '"abc123"',
                "StorageClass": "STANDARD"
            }]
        }
        
        manager = S3Manager(region="us-east-1")
        result = manager.list_objects("meu-bucket")
        
        assert len(result) == 1
        assert result[0]["key"] == "chave/arquivo.txt"
        assert result[0]["size"] == 1024

    def test_list_objects_with_prefix(self, mock_aws_session):
        """Testa listar objetos com prefixo."""
        from cloudtool.s3.manager import S3Manager
        
        manager = S3Manager(region="us-east-1")
        manager.list_objects("meu-bucket", "prefixo/")
        
        mock_aws_session.list_objects_v2.assert_called_with(Bucket="meu-bucket", Prefix="prefixo/")

    def test_clean_old_objects(self, mock_aws_session):
        """Testa limpar objetos antigos."""
        from cloudtool.s3.manager import S3Manager
        
        old_date = (datetime.now() - timedelta(days=31)).replace(tzinfo=None)
        
        mock_aws_session.list_objects_v2.return_value = {
            "Contents": [{
                "Key": "chave/velho.txt",
                "Size": 1024,
                "LastModified": old_date.isoformat(),
                "ETag": '"abc123"',
                "StorageClass": "STANDARD"
            }]
        }
        
        manager = S3Manager(region="us-east-1")
        result = manager.clean_old_objects("meu-bucket", 30)
        
        assert result["status"] == "success"
        assert result["deleted"] == 1

    def test_get_bucket_size(self, mock_aws_session):
        """Testa obter tamanho do bucket."""
        from cloudtool.s3.manager import S3Manager
        
        mock_aws_session.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "file1.txt", "Size": 1024},
                {"Key": "file2.txt", "Size": 2048},
            ]
        }
        
        manager = S3Manager(region="us-east-1")
        result = manager.get_bucket_size("meu-bucket")
        
        assert result["object_count"] == 2
        assert result["total_size_bytes"] == 3072