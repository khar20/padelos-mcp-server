from pydantic import BaseModel
from typing import Optional

class MemberSchema(BaseModel):
    member_id: int
    full_name: str
    phone_number: Optional[str]
    skill_level: Optional[str]
    status: str

class MatchRequestInfo(BaseModel):
    request_id: int
    status: str