from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from database import AsyncSessionLocal
import logic
import schemas

mcp = FastMCP("PadelClubManager")

async def with_db(func, *args, **kwargs):
    async with AsyncSessionLocal() as session:
        return await func(session, *args, **kwargs)

# MCP Tools

@mcp.tool()
async def search_member_by_phone(phone_number: str) -> Optional[schemas.MemberSchema]:
    """Search for a club member by phone number."""
    return await with_db(logic.find_member_by_phone, phone_number)

@mcp.tool()
async def find_candidates(skill_level: str, exclude_member_id: int) -> List[schemas.MemberSchema]:
    """
    Find active matchmaking candidates (excludes the requester).
    Returns list of members (id, name, phone, skill).
    """
    return await with_db(logic.find_candidates, skill_level, exclude_member_id)

@mcp.tool()
async def create_match_request(requester_phone: str, match_datetime: str) -> str:
    """
    Create a matchmaking request. 
    Steps:
    1. Finds member_id from phone.
    2. Creates request.
    Returns request_id or error.
    """
    async with AsyncSessionLocal() as session:
        member = await logic.find_member_by_phone(session, requester_phone)
        if not member:
            return "Error: Member not found with this phone number."
        
        req_id = await logic.create_request(session, member.member_id, match_datetime)
        return str(req_id)

@mcp.tool()
async def save_invitations(request_id: int, invited_phones: List[str]) -> str:
    """
    Send invitations to a list of phone numbers for a specific request.
    Automatically finds the member IDs associated with the phones.
    """
    return await with_db(logic.invite_players_by_phone, request_id, invited_phones)

@mcp.tool()
async def update_invitation_status(request_id: int, invited_phone: str, status: str) -> str:
    """
    Update status (Aceptada/Rechazada) for an invitation.
    Uses phone number to identify the invitee.
    """
    return await with_db(logic.update_status_by_phone, request_id, invited_phone, status)

@mcp.tool()
async def check_availability_and_reserve(start_time: str, end_time: str, member_ids: List[int], court_id: Optional[int] = None) -> str:
    """
    Checks court availability and creates a reservation.
    start_time/end_time format: ISO string (e.g. 2024-01-01T10:00:00+00:00).
    """
    return await with_db(logic.reserve_court, start_time, end_time, member_ids, court_id)

if __name__ == "__main__":
    mcp.run()