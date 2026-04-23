from datetime import datetime

def get_demo_data():
    """Retorna dados fictícios para demonstração do dashboard."""
    return {
        "ec2_instances": [
            {"id": "i-0a1b2c3d4e5f6g7h8", "type": "t3.medium", "state": "running", "az": "us-east-1a", "name": "prod-api-server-01"},
            {"id": "i-1a2b3c4d5e6f7g8h9", "type": "t3.large", "state": "running", "az": "us-east-1b", "name": "prod-worker-01"},
            {"id": "i-9z8y7x6w5v4u3t2s1", "type": "m5.xlarge", "state": "running", "az": "us-east-1a", "name": "prod-db-proxy"},
            {"id": "i-11223344556677889", "type": "t2.micro", "state": "running", "az": "us-east-1c", "name": "bastion-host"},
        ],
        "ec2_volumes": [
            {"id": "vol-0123456789abcdef0", "size": 100, "type": "gp3", "state": "in-use"},
            {"id": "vol-abcdef01234567890", "size": 500, "type": "io2", "state": "in-use"},
            {"id": "vol-9876543210fedcba0", "size": 20, "type": "gp2", "state": "available"},
        ],
        "s3_buckets": [
            {"name": "prod-assets-static", "created": "2023-01-15"},
            {"name": "company-backups-db", "created": "2023-02-20"},
            {"name": "user-uploads-raw", "created": "2023-05-10"},
            {"name": "cloudtool-logs-audit", "created": "2024-01-05"},
        ],
        "rds_instances": [
            {"id": "prod-postgres-main", "type": "db.m5.large", "engine": "postgres", "state": "available", "az": "us-east-1a"},
            {"id": "staging-mysql-01", "type": "db.t3.medium", "engine": "mysql", "state": "available", "az": "us-east-1b"},
        ],
        "iam_users": [
            {"name": "admin-user", "created": "2023-01-01"},
            {"name": "dev-backup-bot", "created": "2023-06-15"},
            {"name": "readonly-auditor", "created": "2024-02-10"},
        ],
        "iam_roles": [
            {"name": "EC2FullAccessRole", "created": "2023-01-01"},
            {"name": "S3ReadOnlyRole", "created": "2023-03-12"},
            {"name": "LambdaExecutionRole", "created": "2023-11-20"},
        ],
        "iam_groups": [
            {"name": "Administrators", "created": "2023-01-01"},
            {"name": "Developers", "created": "2023-05-05"},
        ],
        "cloudwatch_alarms": [
            {"name": "High-CPU-Usage-API", "state": "OK", "metric": "CPUUtilization", "namespace": "AWS/EC2"},
            {"name": "RDS-Storage-Low", "state": "ALARM", "metric": "FreeStorageSpace", "namespace": "AWS/RDS"},
            {"name": "S3-Errors-Upload", "state": "OK", "metric": "5xxErrors", "namespace": "AWS/S3"},
        ],
        "cloudwatch_logs": [
            {"name": "/aws/lambda/process-orders", "retention": 14},
            {"name": "/aws/ec2/api-server/access.log", "retention": 30},
            {"name": "cloudtool-audit-trail", "retention": 365},
        ],
        "ecr_repos": [
            {"name": "cloudtool/api-core", "uri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/cloudtool/api-core"},
            {"name": "cloudtool/worker-node", "uri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/cloudtool/worker-node"},
        ],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
