from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (
        CheckConstraint(
            "length(trim(interest)) > 0",
            name="ck_user_interests_interest_not_blank",
        ),
        CheckConstraint(
            "length(trim(normalized_interest)) > 0",
            name="ck_user_interests_normalized_not_blank",
        ),
        CheckConstraint("position >= 0", name="ck_user_interests_position_nonnegative"),
        UniqueConstraint(
            "user_id",
            "normalized_interest",
            name="uq_user_interests_user_normalized_interest",
        ),
        UniqueConstraint("user_id", "position", name="uq_user_interests_user_position"),
        Index("ix_user_interests_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    interest: Mapped[str] = mapped_column(String(80), nullable=False)
    normalized_interest: Mapped[str] = mapped_column(String(240), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
