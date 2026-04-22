"""Teste local sem API AWS real - usa moto para S3"""
from moto import mock_aws
import boto3
import tempfile
import os


@mock_aws
def test_s3_list():
    """Testa listar buckets S3."""
    from cloudtool.s3.manager import S3Manager
    
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="meu-bucket-teste")
    s3.put_object(Bucket="meu-bucket-teste", Key="teste.txt", Body=b"conteudo")
    
    manager = S3Manager(region="us-east-1")
    buckets = manager.list_buckets()
    
    print(f"Buckets: {len(buckets)}")
    assert len(buckets) == 1
    print(f"Nome: {buckets[0]['name']}")
    
    objects = manager.list_objects("meu-bucket-teste")
    print(f"Objetos: {len(objects)}")
    print("[OK] S3 list passed")


@mock_aws
def test_s3_upload_download():
    """Testa upload e download S3."""
    from cloudtool.s3.manager import S3Manager
    
    with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt") as f:
        f.write("conteudo de teste")
        temp_file = f.name
    
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="meu-bucket-teste")
    
    manager = S3Manager(region="us-east-1")
    
    result = manager.upload_file(temp_file, "meu-bucket-teste")
    print(f"Upload: {result['status']}")
    assert result["status"] == "success"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        download_file = f.name

    result = manager.download_file("meu-bucket-teste", os.path.basename(temp_file), download_file)
    print(f"Download: {result['status']}")

    os.unlink(temp_file)
    os.unlink(download_file)
    print("[OK] S3 upload/download passed")


@mock_aws
def test_s3_sync():
    """Testa sincronização S3."""
    from cloudtool.s3.manager import S3Manager
    
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="meu-bucket-teste")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
            f.write("conteudo 1")
        with open(os.path.join(tmpdir, "file2.txt"), "w") as f:
            f.write("conteudo 2")
        
        manager = S3Manager(region="us-east-1")
        result = manager.sync_directory(tmpdir, "meu-bucket-teste")
        
        print(f"Enviados: {result['uploaded']}")
        assert result["uploaded"] == 2
        print("[OK] S3 sync passed")


if __name__ == "__main__":
    test_s3_list()
    test_s3_upload_download()
    test_s3_sync()
    print("\n[OK] Todos os testes locais passaram!")