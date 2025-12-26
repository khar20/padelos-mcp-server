from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models import Member, MatchRequest, MatchInvitation, Reservation, Court, ReservationMember, ReservationMember
from schemas import MemberSchema

# --- Member Logic ---
async def find_member_by_phone(session: AsyncSession, phone: str) -> Optional[MemberSchema]:
    """Finds a member by phone. Returns the first active one found."""
    stmt = select(Member).where(Member.phone_number == phone).limit(1)
    result = await session.scalar(stmt)
    
    if result:
        return MemberSchema(
            member_id=result.member_id,
            full_name=result.full_name,
            phone_number=result.phone_number,
            skill_level=result.skill_level,
            status=result.status
        )
    return None

async def find_candidates(session: AsyncSession, skill_level: str, exclude_id: int) -> List[MemberSchema]:
    """Finds up to 3 active candidates of the same skill level."""
    stmt = (
        select(Member)
        .where(and_(
            Member.skill_level == skill_level,
            Member.member_id != exclude_id,
            Member.status == 'Activo' # Matches 'member_status' logic
        ))
        .limit(3)
    )
    results = await session.scalars(stmt)
    return [
        MemberSchema(
            member_id=m.member_id,
            full_name=m.full_name,
            phone_number=m.phone_number,
            skill_level=m.skill_level,
            status=m.status
        ) for m in results
    ]

# --- Matchmaking Logic ---
async def create_request(session: AsyncSession, member_id: int, dt_str: str) -> int:
    """Creates a match request linked to member_id."""
    match_dt = datetime.fromisoformat(dt_str)
    async with session.begin():
        req = MatchRequest(requester_id=member_id, match_datetime=match_dt)
        session.add(req)
        await session.flush()
        return req.request_id

async def invite_players_by_phone(session: AsyncSession, request_id: int, phones: List[str]) -> str:
    """
    Look up member IDs by phone numbers and create invitations.
    Ignores numbers that don't match a member.
    """
    async with session.begin():
        # Find member_ids for these phones
        stmt = select(Member.member_id, Member.phone_number).where(Member.phone_number.in_(phones))
        results = await session.execute(stmt)
        found_members = results.all() # [(id, phone), ...]

        count = 0
        for m_id, _ in found_members:
            inv = MatchInvitation(request_id=request_id, invited_member_id=m_id)
            session.add(inv)
            count += 1
            
        return f"Created {count} invitations. (Found {count}/{len(phones)} members)"

async def update_status_by_phone(session: AsyncSession, request_id: int, phone: str, status: str) -> str:
    """Updates invitation status based on the responder's phone."""
    async with session.begin():
        # Join Invitation -> Member to filter by Phone
        stmt = (
            select(MatchInvitation)
            .join(Member, MatchInvitation.invited_member_id == Member.member_id)
            .where(and_(
                MatchInvitation.request_id == request_id,
                Member.phone_number == phone
            ))
        )
        inv = await session.scalar(stmt)
        
        if not inv:
            return "Invitation not found for this phone number."
            
        inv.status = status
        return f"Status updated to {status}"

# --- Reservation Logic ---
async def reserve_court(session: AsyncSession, start: str, end: str, member_ids: List[int], court_id: Optional[int] = None) -> str:
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    
    async with session.begin():
        # 1. Define overlap conflict
        # (StartA < EndB) and (EndA > StartB)
        conflict = and_(
            Reservation.status == 'Confirmada',
            Reservation.start_time < end_dt,
            Reservation.end_time > start_dt
        )
        
        target_court = court_id
        
        if not target_court:
            # Find a court that has NO conflicting reservations
            busy_courts_subq = select(Reservation.court_id).where(conflict)
            
            # Select first available court
            stmt = select(Court.court_id).where(
                and_(
                    Court.status == 'Disponible',
                    Court.court_id.not_in(busy_courts_subq)
                )
            ).limit(1)
            
            target_court = await session.scalar(stmt)
            
            if not target_court:
                return "No available courts for this time slot."
        else:
            # Check specific court availability
            is_busy = await session.scalar(
                select(Reservation)
                .where(and_(Reservation.court_id == target_court, conflict))
            )
            if is_busy:
                return f"Court {target_court} is already reserved."

        # 2. Create Reservation
        res = Reservation(
            court_id=target_court, 
            start_time=start_dt, 
            end_time=end_dt,
            status='Confirmada'
        )
        session.add(res)
        await session.flush() # Get ID
        
        # 3. Add Members
        for mid in member_ids:
            session.add(ReservationMember(reservation_id=res.reservation_id, member_id=mid))
            
        return f"Reservation {res.reservation_id} confirmed on Court {target_court}."