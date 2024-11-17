from argon2 import PasswordHasher
from models import DBUser, UserInfo
from base64 import b64decode
from fastapi import HTTPException
import requests

def hash_password(hasher: PasswordHasher, password: str) -> str:
    return hasher.hash(password)

def verify_password(hasher: PasswordHasher, given_password, password_hash):
    return hasher.verify(hash=password_hash, password=given_password)

def db_response_to_user_info(db_response: dict) -> UserInfo:
    user_info = UserInfo(username=db_response['_id'], friendly_name=db_response['friendly_name'], simplefin_access_url=db_response['simplefin_access_url'])
    return user_info

def exchange_simplefin_setup(simplefin_setup_token: str) -> str:
    claim_url = b64decode(simplefin_setup_token)
    print(f"Received SimpleFIN claim URL: {claim_url}")
    response = requests.post(claim_url, headers={"Content-Length": "0"})
    if not response.ok:
        raise HTTPException(status_code=400, detail="Unable to exchange SimpleFIN token for access URL")
    simplefin_access_url = response.text
    return simplefin_access_url