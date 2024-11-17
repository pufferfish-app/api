from argon2 import PasswordHasher
from models import *
from base64 import b64decode
from fastapi import HTTPException
import requests
import json

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
    response = requests.post(claim_url)
    if not response.ok:
        raise HTTPException(status_code=400, detail="Unable to exchange SimpleFIN token for access URL")
    simplefin_access_url = response.text
    return simplefin_access_url

def get_simplefin_data(simplefin_access_url: str) -> dict:
    if simplefin_access_url == "https://fake_data:fake_data@beta-bridge.simplefin.org/simplefin":
        # Respond with mock data if a specific nonexistent SimpleFIN URL is used
        fraud_data_path = 'mock_data/fraud.json'
        with open(fraud_data_path) as f:
            data = json.load(f)
            print(f"Loaded mock data from {fraud_data_path}")
    else:
        # Else, get data from SimpleFIN
        response = requests.get(simplefin_access_url)
        if not response.ok:
            raise HTTPException(status_code=400, detail="Unable to get data from SimpleFIN")
        data = response.text
    
    return data

def get_frontpage_data(simplefin_access_url: str) -> FrontpageData:
    # Get data from SimpleFIN
    raw_data = get_simplefin_data(simplefin_access_url)

    # Populate model from raw data
    account = raw_data["accounts"][0]
    transactions = import_transactions_from_dict(account["transactions"])
    frontpage_data = FrontpageData(
        account_name = account["name"],
        balance = account["balance"],
        available_balance = account["available-balance"],
        currency = account["currency"],
        balance_date = account["balance-date"],
        recent_transactions = transactions[0:3] if len(transactions) > 3 else transactions
    )

    return frontpage_data

def import_transactions_from_dict(transaction_dicts: list[dict]) -> list[Transaction]:
    # Convert transactions into Transaction objects
    print(transaction_dicts)
    transactions = [Transaction(**transaction) for transaction in transaction_dicts]

    # Sort them by time, newest to oldest
    sorted_transactions = sorted(transactions, key=lambda t:t.posted)
    sorted_transactions.reverse()

    return sorted_transactions