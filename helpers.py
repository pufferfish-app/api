from argon2 import PasswordHasher
from models import DBUser, UserInfo

def hash_password(hasher: PasswordHasher, password: str) -> str:
    return hasher.hash(password)

def verify_password(hasher: PasswordHasher, given_password, password_hash):
    return hasher.verify(hash=password_hash, password=given_password)

def db_response_to_user_info(db_response: dict) -> UserInfo:
    user_info = UserInfo(username=db_response['_id'], friendly_name=db_response['friendly_name'], simplefin_access_url=db_response['simplefin_access_url'])
    return user_info