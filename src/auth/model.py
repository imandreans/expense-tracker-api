from pydantic import BaseModel, Field, BeforeValidator
from uuid import UUID
from typing import Optional
import re
from typing import Annotated

def check_whitespaces(text: str) -> str:
    if re.search(r"\\S+", text):
        raise ValueError("No whitespaces, please")
    return text

class RegisterUserRequest(BaseModel):
    # username: Annotated[str, BeforeValidator(check_whitespaces)] = Field(min_length=1, frozen=True)
    username: str = Field(min_length=1, frozen=True)
    password: str = Field(min_length=8)
    balance: int = Field(gt=0, repr=True)

class Token(BaseModel):
    create_access: str
    token_type: str

class LoginUserRequest(BaseModel):
    username: str = Field(min_length=1, frozen=True)
    password: str = Field(min_length=8)

class TokenData(BaseModel):
    user_id: Optional[str] = None    
    def get_uuid(self) -> UUID | None:
        if self.user_id:
            return UUID(self.user_id)
        return None
    
