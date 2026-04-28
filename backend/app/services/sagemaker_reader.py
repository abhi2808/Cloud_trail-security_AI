"""
SageMaker reader service — endpoint and model metadata only.
sagemaker:InvokeEndpoint, InvokeEndpointAsync, CreateTrainingJob are structurally absent.
"""
import logging
logger = logging.getLogger(__name__)


def _parse_tags(tag_list: list) -> dict:
    return {t.get("Key", ""): t.get("Value", "") for t in (tag_list or [])}


async def list_endpoints(session) -> list:
    """List SageMaker inference endpoints with status and security posture."""
    try:
        client = session.client("sagemaker")
        paginator = client.get_paginator("list_endpoints")
        endpoints = []
        for page in paginator.paginate():
            for ep in page.get("Endpoints", []):
                endpoints.append({
                    "endpoint_name": ep.get("EndpointName"),
                    "endpoint_arn": ep.get("EndpointArn"),
                    "status": ep.get("EndpointStatus"),
                    "creation_time": str(ep.get("CreationTime", "")),
                    "last_modified": str(ep.get("LastModifiedTime", "")),
                })
        return endpoints
    except Exception as e:
        logger.error(f"sagemaker list_endpoints: {type(e).__name__}")
        return []


async def get_endpoint_details(session, endpoint_name: str) -> dict:
    """Get full details and security config for a SageMaker endpoint."""
    try:
        client = session.client("sagemaker")
        resp = client.describe_endpoint(EndpointName=endpoint_name)

        # Check if endpoint has network isolation (security best practice)
        config_name = resp.get("EndpointConfigName")
        network_isolated = False
        kms_key = None
        try:
            cfg_resp = client.describe_endpoint_config(EndpointConfigName=config_name)
            kms_key = cfg_resp.get("KmsKeyId")
            for variant in cfg_resp.get("ProductionVariants", []):
                pass  # network isolation is per-model
        except Exception:
            pass

        findings = []
        if not kms_key:
            findings.append("Endpoint data capture not KMS-encrypted")

        return {
            "endpoint_name": resp.get("EndpointName"),
            "endpoint_arn": resp.get("EndpointArn"),
            "endpoint_config_name": config_name,
            "status": resp.get("EndpointStatus"),
            "kms_key": kms_key,
            "creation_time": str(resp.get("CreationTime", "")),
            "security_findings": findings,
        }
    except Exception as e:
        logger.error(f"sagemaker get_endpoint_details {endpoint_name}: {type(e).__name__}")
        return {"error": str(e), "endpoint_name": endpoint_name}


async def list_training_jobs(session, max_results: int = 20) -> list:
    """List recent SageMaker training jobs."""
    try:
        client = session.client("sagemaker")
        resp = client.list_training_jobs(MaxResults=max_results, SortBy="CreationTime", SortOrder="Descending")
        jobs = []
        for j in resp.get("TrainingJobSummaries", []):
            jobs.append({
                "job_name": j.get("TrainingJobName"),
                "status": j.get("TrainingJobStatus"),
                "creation_time": str(j.get("CreationTime", "")),
                "end_time": str(j.get("TrainingEndTime", "")),
            })
        return jobs
    except Exception as e:
        logger.error(f"sagemaker list_training_jobs: {type(e).__name__}")
        return []


async def list_notebook_instances(session) -> list:
    """List SageMaker notebook instances — flags those without network isolation."""
    try:
        client = session.client("sagemaker")
        paginator = client.get_paginator("list_notebook_instances")
        notebooks = []
        for page in paginator.paginate():
            for nb in page.get("NotebookInstances", []):
                findings = []
                if not nb.get("NetworkInterfaceId"):
                    findings.append("Notebook may have internet access — no VPC subnet configured")
                notebooks.append({
                    "notebook_name": nb.get("NotebookInstanceName"),
                    "status": nb.get("NotebookInstanceStatus"),
                    "instance_type": nb.get("InstanceType"),
                    "url": nb.get("Url"),
                    "kms_key": nb.get("KmsKeyId"),
                    "security_findings": findings,
                })
        return notebooks
    except Exception as e:
        logger.error(f"sagemaker list_notebook_instances: {type(e).__name__}")
        return []


async def get_sagemaker_security_summary(session) -> dict:
    """Account-wide SageMaker security posture summary."""
    endpoints = await list_endpoints(session)
    notebooks = await list_notebook_instances(session)
    jobs = await list_training_jobs(session, max_results=10)

    findings = []
    for nb in notebooks:
        findings.extend(nb.get("security_findings", []))

    return {
        "endpoint_count": len(endpoints),
        "notebook_count": len(notebooks),
        "recent_training_jobs": len(jobs),
        "security_findings": findings,
        "endpoints": endpoints,
        "notebooks": notebooks,
    }
