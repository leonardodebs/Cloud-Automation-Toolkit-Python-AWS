"""
CloudTool Dashboard - Visualization Web Interface
Run: streamlit run web_dashboard/app.py
"""
import streamlit as st
import boto3
from datetime import datetime


st.set_page_config(
    page_title="CloudTool Dashboard",
    page_icon="cloud",
    layout="wide",
    initial_sidebar_state="expanded",
)


class AWSClient:
    """Cliente AWS com cache."""

    def __init__(self, region="us-east-1", profile=None):
        self.region = region
        if profile:
            self.session = boto3.Session(profile_name=profile, region_name=region)
        else:
            self.session = boto3.Session(region_name=region)

    @property
    def ec2(self):
        return self.session.client("ec2")

    @property
    def s3(self):
        return self.session.client("s3")

    @property
    def rds(self):
        return self.session.client("rds")

    @property
    def iam(self):
        return self.session.client("iam")

    @property
    def cw(self):
        return self.session.client("cloudwatch")

    @property
    def logs(self):
        return self.session.client("logs")

    @property
    def ecr(self):
        return self.session.client("ecr")


@st.cache_data(ttl=60)
def get_aws_data():
    """Carrega todos os dados da AWS."""
    client = AWSClient()

    data = {}

    try:
        ec2_resp = client.ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        instances = []
        for res in ec2_resp.get("Reservations", []):
            for inst in res.get("Instances", []):
                tags = inst.get("Tags", [])
                name_value = "N/A"
                for t in tags:
                    if t.get("Key") == "Name":
                        name_value = t.get("Value", "N/A")
                        break
                instances.append({
                    "id": inst.get("InstanceId"),
                    "type": inst.get("InstanceType"),
                    "state": inst.get("State", {}).get("Name"),
                    "az": inst.get("Placement", {}).get("AvailabilityZone"),
                    "name": name_value,
                })
        data["ec2_instances"] = instances
    except Exception:
        data["ec2_instances"] = []

    try:
        vol_resp = client.ec2.describe_volumes()
        data["ec2_volumes"] = [{
            "id": v.get("VolumeId"),
            "size": v.get("Size"),
            "type": v.get("VolumeType"),
            "state": v.get("State"),
        } for v in vol_resp.get("Volumes", [])]
    except Exception:
        data["ec2_volumes"] = []

    try:
        buckets = client.s3.list_buckets().get("Buckets", [])
        data["s3_buckets"] = [{
            "name": b.get("Name"),
            "created": b.get("CreationDate").strftime("%Y-%m-%d"),
        } for b in buckets]
    except Exception:
        data["s3_buckets"] = []

    try:
        rds_resp = client.rds.describe_db_instances()
        data["rds_instances"] = [{
            "id": db.get("DBInstanceIdentifier"),
            "type": db.get("DBInstanceClass"),
            "engine": db.get("Engine"),
            "state": db.get("DBInstanceStatus"),
            "az": db.get("AvailabilityZone"),
        } for db in rds_resp.get("DBInstances", [])]
    except Exception:
        data["rds_instances"] = []

    try:
        users = client.iam.list_users().get("Users", [])
        roles = client.iam.list_roles().get("Roles", [])
        groups = client.iam.list_groups().get("Groups", [])
        data["iam_users"] = [{"name": u.get("UserName"), "created": u.get("CreateDate").strftime("%Y-%m-%d")} for u in users]
        data["iam_roles"] = [{"name": r.get("RoleName"), "created": r.get("CreateDate").strftime("%Y-%m-%d")} for r in roles]
        data["iam_groups"] = [{"name": g.get("GroupName"), "created": g.get("CreateDate").strftime("%Y-%m-%d")} for g in groups]
    except Exception:
        data["iam_users"] = []
        data["iam_roles"] = []
        data["iam_groups"] = []

    try:
        alarms = client.cw.describe_alarms().get("MetricAlarms", [])
        data["cloudwatch_alarms"] = [{
            "name": a.get("AlarmName"),
            "state": a.get("StateValue"),
            "metric": a.get("MetricName"),
            "namespace": a.get("Namespace"),
        } for a in alarms]
    except Exception:
        data["cloudwatch_alarms"] = []

    try:
        data["cloudwatch_logs"] = [
            {"name": g.get("logGroupName"), "retention": g.get("retentionInDays")}
            for g in client.logs.describe_log_groups().get("logGroups", [])
        ][:20]
    except Exception:
        data["cloudwatch_logs"] = []

    try:
        repos = client.ecr.describe_repositories().get("repositories", [])
        data["ecr_repos"] = [{"name": r.get("repositoryName"), "uri": r.get("repositoryUri")} for r in repos]
    except Exception:
        data["ecr_repos"] = []

    data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return data


def sidebar():
    """Sidebar com navegação."""
    st.logo("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", size="large")

    st.sidebar.title("CloudTool")
    st.sidebar.caption("Dashboard de Infraestrutura AWS")

    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navegação",
        ["Overview", "EC2", "S3", "RDS", "IAM", "CloudWatch", "ECR"],
        captions=[
            "Resumo geral",
            "Instâncias e Volumes",
            "Buckets e Objetos",
            "Bancos de Dados",
            "Usuários e Permissões",
            "Monitoramento",
            "Container Registry",
        ],
    )

    st.sidebar.divider()

    with st.sidebar.expander("Configurações"):
        region = st.selectbox("Região", ["us-east-1", "us-west-2", "sa-east-1"], index=0)

    st.sidebar.caption(f"Atualizado: {get_aws_data()['timestamp']}")

    return page, region


def overview_page(data):
    """Página de overview."""
    st.title("CloudTool Dashboard")
    st.caption("Visão geral da sua infraestrutura AWS")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("EC2 Rodando", len(data["ec2_instances"]))

    with col2:
        st.metric("Buckets S3", len(data["s3_buckets"]))

    with col3:
        st.metric("Instâncias RDS", len(data["rds_instances"]))

    with col4:
        st.metric("Usuários IAM", len(data["iam_users"]))

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("EC2 em Execução")
        if data["ec2_instances"]:
            st.dataframe(
                data["ec2_instances"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhuma instância em execução")

    with c2:
        st.subheader("S3 Buckets")
        if data["s3_buckets"]:
            st.dataframe(
                data["s3_buckets"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhum bucket encontrado")


def ec2_page(data):
    """Página EC2."""
    tab1, tab2 = st.tabs(["Instâncias", "Volumes"])

    with tab1:
        st.subheader("Instâncias EC2")

        if data["ec2_instances"]:
            st.dataframe(
                data["ec2_instances"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhuma instância em execução")

    with tab2:
        st.subheader("Volumes EBS")

        if data["ec2_volumes"]:
            st.dataframe(
                data["ec2_volumes"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhum volume encontrado")


def s3_page(data):
    """Página S3."""
    st.subheader("Buckets S3")

    if data["s3_buckets"]:
        st.dataframe(
            data["s3_buckets"],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Nenhum bucket encontrado")


def rds_page(data):
    """Página RDS."""
    st.subheader("Instâncias RDS")

    if data["rds_instances"]:
        st.dataframe(
            data["rds_instances"],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Nenhuma instância RDS encontrada")


def iam_page(data):
    """Página IAM."""
    tab1, tab2, tab3 = st.tabs(["Usuários", "Roles", "Grupos"])

    with tab1:
        st.subheader("Usuários IAM")
        if data["iam_users"]:
            st.dataframe(
                data["iam_users"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhum usuário encontrado")

    with tab2:
        st.subheader("Roles IAM")
        if data["iam_roles"]:
            st.dataframe(
                data["iam_roles"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhuma role encontrada")

    with tab3:
        st.subheader("Grupos IAM")
        if data["iam_groups"]:
            st.dataframe(
                data["iam_groups"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhum grupo encontrado")


def cloudwatch_page(data):
    """Página CloudWatch."""
    tab1, tab2 = st.tabs(["Alarmes", "Log Groups"])

    with tab1:
        st.subheader("Alarmes CloudWatch")
        if data["cloudwatch_alarms"]:
            st.dataframe(
                data["cloudwatch_alarms"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhum alarme encontrado")

    with tab2:
        st.subheader("Grupos de Logs")
        if data["cloudwatch_logs"]:
            st.dataframe(
                data["cloudwatch_logs"],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("Nenhum grupo de logs encontrado")


def ecr_page(data):
    """Página ECR."""
    st.subheader("Repositórios ECR")

    if data["ecr_repos"]:
        st.dataframe(
            data["ecr_repos"],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("Nenhum repositório ECR encontrado")


def main():
    """Main app."""
    page, region = sidebar()
    data = get_aws_data()

    if page == "Overview":
        overview_page(data)
    elif page == "EC2":
        ec2_page(data)
    elif page == "S3":
        s3_page(data)
    elif page == "RDS":
        rds_page(data)
    elif page == "IAM":
        iam_page(data)
    elif page == "CloudWatch":
        cloudwatch_page(data)
    elif page == "ECR":
        ecr_page(data)


if __name__ == "__main__":
    main()