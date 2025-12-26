from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Date, ForeignKey, Text, CheckConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP, ENUM

class Base(DeclarativeBase):
    pass

class Member(Base):
    __tablename__ = "members"
    
    member_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    level_category: Mapped[Optional[str]] = mapped_column(String(20))
    skill_level: Mapped[Optional[str]] = mapped_column(String(20))
    
    status: Mapped[str] = mapped_column(
        ENUM(name='member_status', create_type=False), 
        default='Pendiente'
    )
    
    membership: Mapped[str] = mapped_column(
        ENUM(name='membership_type', create_type=False)
    )
    
    join_date: Mapped[date] = mapped_column(Date)
    membership_expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

class Court(Base):
    __tablename__ = "courts"
    
    court_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    
    status: Mapped[str] = mapped_column(
        ENUM(name='court_status', create_type=False), 
        default='Disponible'
    )
    
    type: Mapped[Optional[str]] = mapped_column(String(50), default='Pádel')

class Reservation(Base):
    __tablename__ = "reservations"
    
    reservation_id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.court_id", ondelete="RESTRICT"))
    start_time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    end_time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    
    status: Mapped[str] = mapped_column(
        ENUM(name='reservation_status', create_type=False), 
        default='Pendiente'
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('end_time > start_time', name='check_times'),
    )

class ReservationMember(Base):
    __tablename__ = "reservation_members"
    
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.reservation_id", ondelete="CASCADE"), primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.member_id", ondelete="CASCADE"), primary_key=True)

# Auxiliary Tables

class MatchRequest(Base):
    __tablename__ = "match_requests"

    request_id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("members.member_id"))
    match_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    status: Mapped[str] = mapped_column(String, default="Pending")

    requester: Mapped["Member"] = relationship()
    invitations: Mapped[List["MatchInvitation"]] = relationship(back_populates="request")

class MatchInvitation(Base):
    __tablename__ = "match_invitations"

    invitation_id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("match_requests.request_id"))
    invited_member_id: Mapped[int] = mapped_column(ForeignKey("members.member_id"))
    status: Mapped[str] = mapped_column(String, default="Pending")

    request: Mapped["MatchRequest"] = relationship(back_populates="invitations")
    invited_member: Mapped["Member"] = relationship()