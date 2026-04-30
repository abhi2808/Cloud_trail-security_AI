import boto3
from botocore.exceptions import ClientError

def verify_credentials(access_key: str, secret_key: str, region: str) -> tuple[bool, str]:
    """Tests if the provided credentials can successfully access CloudTrail."""
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        client = session.client("cloudtrail")
        client.list_trails()
        return True, "Connection verified. CloudTrail access confirmed."
        
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', 'Unknown')
        if code == 'AccessDeniedException':
             return False, "Credentials valid but missing CloudTrail permissions. Check IAM policy."
        elif code in ['InvalidClientTokenId', 'SignatureDoesNotMatch']:
             return False, "Invalid Access Key or Secret Key."
        return False, f"Connection failed: {str(e)}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
