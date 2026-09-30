from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Community(Base):
    __tablename__ = "communities"
    __table_args__ = (
        CheckConstraint(
            "access_type IN ('open', 'invite_only')",
            name="ck_communities_access_type",
        ),
        CheckConstraint("length(trim(name)) > 0", name="ck_communities_name_not_blank"),
        CheckConstraint("length(trim(slug)) > 0", name="ck_communities_slug_not_blank"),
        CheckConstraint("length(trim(topic)) > 0", name="ck_communities_topic_not_blank"),
        UniqueConstraint("slug", name="uq_communities_slug"),
        Index("ix_communities_owner_id", "owner_id"),
        Index("ix_communities_topic", "topic"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    topic: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        server_default=text("''"),
    )
    access_type: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
