"""CloudTool - Kit de Automação AWS

Uma ferramenta CLI abrangente para automatizar tarefas comuns de infraestrutura AWS.
"""

__version__ = "1.0.0"
__author__ = "Cloud Engineer"

from .ec2.manager import EC2Manager
from .s3.manager import S3Manager
from .reports.generator import ReportGenerator

__all__ = ["EC2Manager", "S3Manager", "ReportGenerator"]
