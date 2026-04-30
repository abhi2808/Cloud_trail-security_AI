"""
Bedrock reader service — model metadata only.
bedrock:InvokeModel and bedrock:InvokeModelWithResponseStream are structurally absent.
"""
import logging
logger = logging.getLogger(__name__)


async def list_foundation_models(session) -> list:
    """
    List available Bedrock foundation models including cross-region inference profiles.
    In regions like ap-south-1, models are accessed via APAC cross-region inference
    profiles (e.g. apac.anthropic.claude-3-5-sonnet-...) rather than ON_DEMAND.
    This function fetches both to give a complete picture.
    """
    try:
        client = session.client("bedrock")
        models = []

        # ① Standard ON_DEMAND foundation models
        try:
            resp = client.list_foundation_models(byInferenceType="ON_DEMAND")
            for m in resp.get("modelSummaries", []):
                models.append({
                    "model_id": m.get("modelId"),
                    "model_name": m.get("modelName"),
                    "provider": m.get("providerName"),
                    "inference_type": "ON_DEMAND",
                    "input_modalities": m.get("inputModalities", []),
                    "output_modalities": m.get("outputModalities", []),
                    "response_streaming": m.get("responseStreamingSupported", False),
                })
        except Exception:
            pass

        # ② Cross-region inference profiles (used in ap-south-1 as apac.* prefix)
        try:
            paginator = client.get_paginator("list_inference_profiles")
            for page in paginator.paginate(typeEquals="SYSTEM_DEFINED"):
                for p in page.get("inferenceProfileSummaries", []):
                    models.append({
                        "model_id": p.get("inferenceProfileId"),
                        "model_name": p.get("inferenceProfileName"),
                        "provider": p.get("inferenceProfileId", "").split(".")[0].upper(),  # e.g. APAC
                        "inference_type": "CROSS_REGION",
                        "status": p.get("status"),
                    })
        except Exception:
            pass

        return models
    except Exception as e:
        logger.error(f"bedrock list_foundation_models: {type(e).__name__}")
        return []


async def list_custom_models(session) -> list:
    """List customer fine-tuned Bedrock models."""
    try:
        client = session.client("bedrock")
        paginator = client.get_paginator("list_custom_models")
        models = []
        for page in paginator.paginate():
            for m in page.get("modelSummaries", []):
                models.append({
                    "model_name": m.get("modelName"),
                    "model_arn": m.get("modelArn"),
                    "base_model_arn": m.get("baseModelArn"),
                    "creation_time": str(m.get("creationTime", "")),
                })
        return models
    except Exception as e:
        logger.error(f"bedrock list_custom_models: {type(e).__name__}")
        return []


async def get_invocation_logging_config(session) -> dict:
    """
    Get Bedrock model invocation logging configuration.
    This is a key security control — if logging is disabled, AI model calls are unaudited.
    """
    try:
        client = session.client("bedrock")
        resp = client.get_model_invocation_logging_configuration()
        cfg = resp.get("loggingConfig", {})
        logging_enabled = cfg.get("cloudWatchConfig", {}).get("logGroupName") is not None \
            or cfg.get("s3Config", {}).get("bucketName") is not None

        return {
            "logging_enabled": logging_enabled,
            "cloudwatch_log_group": cfg.get("cloudWatchConfig", {}).get("logGroupName"),
            "s3_bucket": cfg.get("s3Config", {}).get("bucketName"),
            "security_finding": None if logging_enabled else "Bedrock invocation logging is DISABLED — AI model calls are not audited",
        }
    except Exception as e:
        logger.error(f"bedrock get_invocation_logging_config: {type(e).__name__}")
        return {"error": str(e), "logging_enabled": False}


async def get_bedrock_security_summary(session) -> dict:
    """Combined summary: custom models + logging status for security posture."""
    logging_cfg = await get_invocation_logging_config(session)
    custom = await list_custom_models(session)
    foundation = await list_foundation_models(session)
    findings = []
    if not logging_cfg.get("logging_enabled"):
        findings.append("Bedrock invocation logging is disabled — model usage is unaudited")
    return {
        "foundation_model_count": len(foundation),
        "custom_model_count": len(custom),
        "custom_models": custom,
        "logging_config": logging_cfg,
        "security_findings": findings,
    }
