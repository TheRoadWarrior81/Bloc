from pydantic import BaseModel, Field

class UserRegister(BaseModel):
    username: str = Field(min_length=2, max_length=30)
    email: str = Field(max_length=100)
    password: str = Field(min_length=6, max_length=72)

class UserLogin(BaseModel):
    email: str = Field(max_length=100)
    password: str = Field(min_length=6, max_length=72)

class UserUpdate(BaseModel):
    username: str = Field(min_length=2, max_length=30)

class CircleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    invite_code: str | None = Field(default=None, max_length=20)

class JoinByCode(BaseModel):
    invite_code: str = Field(min_length=1, max_length=20)