# Pufferfish API

#-------------#
#   IMPORTS   #
#-------------#

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from models import *
from helpers import *
from detection import *


#------------------------#
#   INITIALIZE FASTAPI   #
#------------------------#

# Creates FastAPI App
app = FastAPI() 
origins = ["*"]

# Allows cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)                                                   


#---------------------#
#   INITIALIZE APIS   #
#---------------------#

# Loads environment variables from a .env file if present for local development
load_dotenv()

# Initialize password hasher
hasher: PasswordHasher = PasswordHasher()

# Connect to mongodb on startup
@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(os.environ.get("ATLAS_URI"))
    app.database = app.mongodb_client[os.environ.get("DB_NAME")]
    print("Connected to the MongoDB database!")
    app.users = app.database['users']
    print("User table initialized!")

# Close mongodb connection on shutdown
@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()


#---------------#
#   ENDPOINTS   #
#---------------#

# Sanity check endpoint to ensure server is accessible
@app.get("/")
async def sanity_check():
    return {
        "message": "Welcome to the Pufferfish API! To read more about the available endpoints, visit https://pufferfish-xurta.ondigitalocean.app/docs"
    }

# Check for valid credentials
@app.get("/credential_check")
async def credential_check(user_auth_details: UserAuthDetails):
    # Check if user exists
    if not app.users.count_documents({ "_id": user_auth_details.username }):
        raise HTTPException(status_code=404, detail="User does not exist")
    user_record = app.users.find_one({ "_id": user_auth_details.username })
    
    # Check if given hashed password matches user's
    db_password_hash = user_record['password_hash']
    try:
        if not verify_password(hasher, user_auth_details.password, db_password_hash):
            raise HTTPException(status_code=403, detail="Incorrect password provided")
    except (VerifyMismatchError, VerificationError) as _v:
        raise HTTPException(status_code=403, detail="Incorrect password provided")
    
    return {
        "message": f"Authenticated {user_record['friendly_name']} successfully!"
    }

# Create a new user
@app.post("/create_user")
async def create_user(user_create_request: UserCreateRequest):
    # Get details from request
    username: str = user_create_request.username
    password: str = user_create_request.password
    friendly_name: str = user_create_request.friendly_name

    # Check if user is in db
    if app.users.count_documents({ "_id": username }):
        raise HTTPException(status_code=409, detail="Username is already taken")

    # Hash password and create user model
    hashed_password: str = hash_password(hasher, password)
    user = DBUser(_id=username, password_hash=hashed_password, friendly_name=friendly_name, simplefin_access_url=None)

    # Create new MongoDB document for user
    encoded_user = jsonable_encoder(user)
    print(encoded_user)
    db_response = app.users.insert_one(encoded_user)
    print(db_response)
    created_user = app.users.find_one(
        {"_id": username}
    )
    print(created_user)

    return db_response_to_user_info(created_user)

# Go through SimpleFIN Bridge setup token flow for user
@app.post("/setup_simplefin")
async def setup_simplefin(user_simplefin_setup: UserSimpleFINSetup):
    # Check if user exists
    user_auth_details = user_simplefin_setup.auth_details
    if not app.users.count_documents({ "_id": user_auth_details.username }):
        raise HTTPException(status_code=404, detail="User does not exist")
    user_record = app.users.find_one({ "_id": user_auth_details.username })
    
    # Check if given hashed password matches user's
    db_password_hash = user_record['password_hash']
    try:
        if not verify_password(hasher, user_auth_details.password, db_password_hash):
            raise HTTPException(status_code=403, detail="Incorrect password provided")
    except (VerifyMismatchError, VerificationError) as _v:
        raise HTTPException(status_code=403, detail="Incorrect password provided")
    print(f"User {user_auth_details.username} authenticated successfully!")

    # Exchange setup token for access token
    simplefin_access_url = exchange_simplefin_setup(user_simplefin_setup.simplefin_setup_token)

    # Add access url to database
    app.users.update_one({ "_id": user_auth_details.username }, { "$set": { "simplefin_access_url": simplefin_access_url } })

    return {
        "message": f"Added SimpleFIN access URL for {user_auth_details.username} successfully!"
    }

# Get frontpage data
@app.get("/frontpage_data")
async def frontpage_data(user_auth_details: UserAuthDetails):
    # Check if user exists
    if not app.users.count_documents({ "_id": user_auth_details.username }):
        raise HTTPException(status_code=404, detail="User does not exist")
    user_record = app.users.find_one({ "_id": user_auth_details.username })
    
    # Check if given hashed password matches user's
    db_password_hash = user_record['password_hash']
    try:
        if not verify_password(hasher, user_auth_details.password, db_password_hash):
            raise HTTPException(status_code=403, detail="Incorrect password provided")
    except (VerifyMismatchError, VerificationError) as _v:
        raise HTTPException(status_code=403, detail="Incorrect password provided")
    
    print(f"Authenticated {user_record['friendly_name']} successfully!")
    
    # Check if user has a SimpleFIN access url
    if not user_record['simplefin_access_url']:
        raise HTTPException(status_code=403, detail="User does not have a SimpleFIN access URL")
    
    frontpage_data = get_frontpage_data(user_record['simplefin_access_url'])
    return frontpage_data

# Get all transactions
@app.get("/transactions")
async def get_transactions(user_auth_details: UserAuthDetails):
    # Check if user exists
    if not app.users.count_documents({ "_id": user_auth_details.username }):
        raise HTTPException(status_code=404, detail="User does not exist")
    user_record = app.users.find_one({ "_id": user_auth_details.username })
    
    # Check if given hashed password matches user's
    db_password_hash = user_record['password_hash']
    try:
        if not verify_password(hasher, user_auth_details.password, db_password_hash):
            raise HTTPException(status_code=403, detail="Incorrect password provided")
    except (VerifyMismatchError, VerificationError) as _v:
        raise HTTPException(status_code=403, detail="Incorrect password provided")
    
    print(f"Authenticated {user_record['friendly_name']} successfully!")
    
    # Check if user has a SimpleFIN access url
    if not user_record['simplefin_access_url']:
        raise HTTPException(status_code=403, detail="User does not have a SimpleFIN access URL")
    
    simplefin_data = get_simplefin_data(user_record['simplefin_access_url'])
    transaction_dicts = simplefin_data["accounts"][0]["transactions"]
    transactions = import_transactions_from_dict(transaction_dicts)
    return transactions

# Scan for possibly fraudulent transactions
@app.post("/detect_fraud")
async def detect_fraud(user_auth_details: UserAuthDetails):
    # Check if user exists
    if not app.users.count_documents({ "_id": user_auth_details.username }):
        raise HTTPException(status_code=404, detail="User does not exist")
    user_record = app.users.find_one({ "_id": user_auth_details.username })
    
    # Check if given hashed password matches user's
    db_password_hash = user_record['password_hash']
    try:
        if not verify_password(hasher, user_auth_details.password, db_password_hash):
            raise HTTPException(status_code=403, detail="Incorrect password provided")
    except (VerifyMismatchError, VerificationError) as _v:
        raise HTTPException(status_code=403, detail="Incorrect password provided")
    
    print(f"Authenticated {user_record['friendly_name']} successfully!")
    
    # Check if user has a SimpleFIN access url
    if not user_record['simplefin_access_url']:
        raise HTTPException(status_code=403, detail="User does not have a SimpleFIN access URL")
    
    simplefin_data = get_simplefin_data(user_record['simplefin_access_url'])
    transaction_dicts = simplefin_data["accounts"][0]["transactions"]
    transactions = import_transactions_from_dict(transaction_dicts)
    possible_fraud_instances = detect_all(transactions)
    return possible_fraud_instances

# Provide an AI summary of a possibly fraudulent transaction
@app.post("/llm_fraud_summary")
async def llm_fraud_summary(summarize_request: PossibleFraudSummarizeRequest):
    # Check if user exists
    if not app.users.count_documents({ "_id": summarize_request.auth_details.username }):
        raise HTTPException(status_code=404, detail="User does not exist")
    user_record = app.users.find_one({ "_id": summarize_request.auth_details.username })
    
    # Check if given hashed password matches user's
    db_password_hash = user_record['password_hash']
    try:
        if not verify_password(hasher, summarize_request.auth_details.password, db_password_hash):
            raise HTTPException(status_code=403, detail="Incorrect password provided")
    except (VerifyMismatchError, VerificationError) as _v:
        raise HTTPException(status_code=403, detail="Incorrect password provided")
    
    print(f"Authenticated {user_record['friendly_name']} successfully!")
    
    # Check if user has a SimpleFIN access url
    if not user_record['simplefin_access_url']:
        raise HTTPException(status_code=403, detail="User does not have a SimpleFIN access URL")

    system_prompt = "You are a helpful AI fraud detection assistant, helping summarize possible instances of fraud in the user's bank transaction history"
    user_prompt = f'''Based on the SimpleFIN transaction data in JSON format that is below the line \"DATA BEGINS HERE\", summarize in a short paragraph for an inexperienced user what factors make the transaction(s) appear to be fraudulent, and what the user can do to remedy the situation.

    DATA BEGINS HERE
    {jsonable_encoder(summarize_request.possible_fraud_instance)}'''

    client = OpenAI(
        api_key=os.environ.get("LLM_API_KEY"),
        base_url=os.environ.get("LLM_BASE_URL")
    )

    responses = client.chat.completions.create(
        model='Meta-Llama-3.1-405B-Instruct',
        messages=[{"role": "system", "content": system_prompt}, {"role":"user", "content":user_prompt}]
    )
    response = responses.choices[0].message.content
    return response