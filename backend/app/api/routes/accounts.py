from fastapi import APIRouter, HTTPException, status, Request
from app.models.account import AccountCreate, AccountResponse, AccountTestResult
from app.db.repositories.account_repository import account_repository
from app.core.encryption import encrypt_value
from app.services import cloudtrail
from botocore.exceptions import ClientError
from typing import List

router = APIRouter()

def get_user_id(request: Request) -> str:
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.user["sub"]

@router.get("", response_model=List[AccountResponse])
async def get_accounts(request: Request):
    user_id = get_user_id(request)
    accounts = await account_repository.get_accounts_by_user(user_id)
    return [
        AccountResponse(
            id=str(acc["_id"]),
            nickname=acc["nickname"],
            region=acc["region"],
            created_at=acc["created_at"],
            last_verified=acc.get("last_verified")
        ) for acc in accounts
    ]

@router.post("", response_model=AccountResponse)
async def create_account(request: Request, account_in: AccountCreate):
    user_id = get_user_id(request)
    enc_access = encrypt_value(account_in.access_key_id)
    enc_secret = encrypt_value(account_in.secret_access_key)
    
    doc = await account_repository.add_account(
        user_id=user_id,
        nickname=account_in.nickname,
        region=account_in.region,
        encrypted_access_key=enc_access,
        encrypted_secret_key=enc_secret
    )
    
    return AccountResponse(
        id=str(doc["_id"]),
        nickname=doc["nickname"],
        region=doc["region"],
        created_at=doc["created_at"],
        last_verified=doc.get("last_verified")
    )

@router.post("/test", response_model=AccountTestResult)
async def test_account(request: Request, account_in: AccountCreate):
    # Ensure authenticated
    user_id = get_user_id(request) 
    test_region = account_in.region if account_in.region and account_in.region != "all" else "ap-south-1"
    client = cloudtrail.get_client_with_credentials(
        access_key_id=account_in.access_key_id,
        secret_key=account_in.secret_access_key,
        region=test_region
    )
    try:
        client.list_trails()
        return AccountTestResult(success=True, message="Connection verified. CloudTrail access confirmed.")
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', 'Unknown')
        if code == 'AccessDeniedException':
             return AccountTestResult(success=False, message="Credentials valid but missing CloudTrail permissions. Check IAM policy.")
        elif code == 'InvalidClientTokenId':
             return AccountTestResult(success=False, message="Invalid Access Key ID.")
        elif code == 'SignatureDoesNotMatch':
             return AccountTestResult(success=False, message="Invalid Secret Access Key.")
        else:
             return AccountTestResult(success=False, message=f"Connection failed: {str(e)}")
    except Exception as e:
        return AccountTestResult(success=False, message=f"Connection failed: {str(e)}")

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(request: Request, account_id: str):
    user_id = get_user_id(request)
    deleted = await account_repository.delete_account(account_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
