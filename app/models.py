from pydantic import BaseModel, Field

class UserInfo(BaseModel):
    username: str
    friendly_name: str
    simplefin_access_url: str | None

class DBUser(BaseModel):
    id: str = Field(alias = "_id")
    password_hash: str
    friendly_name: str
    simplefin_access_url: str | None

class UserCreateRequest(BaseModel):
    username: str
    password: str
    friendly_name: str

class UserAuthDetails(BaseModel):
    username: str
    password: str

class UserSimpleFINSetup(BaseModel):
    auth_details: UserAuthDetails
    simplefin_setup_token: str

class Transaction(BaseModel):
    id: str
    posted: int
    amount: str
    description: str
    payee: str
    memo: str

class FrontpageData(BaseModel):
    account_name: str
    balance: str
    available_balance: str
    currency: str
    balance_date: int
    recent_transactions: list[Transaction]

class PossibleFraudInstance(BaseModel):
    transactions: list[Transaction]
    fraud_type: str # duplicate, suspicious_payee, large_p2p

class PossibleFraudSummarizeRequest(BaseModel):
    auth_details: UserAuthDetails
    possible_fraud_instance: PossibleFraudInstance
    