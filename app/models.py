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