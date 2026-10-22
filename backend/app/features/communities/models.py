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
    column,
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
        UniqueConstraint("public_id", name="uq_communities_public_id"),
        UniqueConstraint("slug", name="uq_communities_slug"),
        Index("ix_communities_owner_id", "owner_id"),
        Index("ix_communities_topic", "topic"),
        Index("ix_communities_archived_at", "archived_at"),
        Index(
            "uq_communities_normalized_name",
            func.lower(func.btrim(column("name"))),
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    public_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
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
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class CommunityMembership(Base):
    __tablename__ = "community_memberships"
    __table_args__ = (
        CheckConstraint(
            "role IN ('owner', 'moderator', 'member')",
            name="ck_community_memberships_role",
        ),
        UniqueConstraint(
            "community_id",
            "user_id",
            name="uq_community_memberships_community_user",
        ),
        Index("ix_community_memberships_user_id", "user_id"),
        Index(
            "uq_community_memberships_single_owner",
            "community_id",
            unique=True,
            postgresql_where=text("role = 'owner'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    community_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CommunityRoleChange(Base):
    __tablename__ = "community_role_changes"
    __table_args__ = (
        CheckConstraint(
            "previous_role IN ('member', 'moderator')",
            name="ck_community_role_changes_previous_role",
        ),
        CheckConstraint(
            "new_role IN ('member', 'moderator')",
            name="ck_community_role_changes_new_role",
        ),
        CheckConstraint(
            "previous_role <> new_role",
            name="ck_community_role_changes_role_changed",
        ),
        Index(
            "ix_community_role_changes_community_changed_at",
            "community_public_id",
            "changed_at",
        ),
        Index("ix_community_role_changes_target_public_id", "target_public_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    community_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
    )
    community_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    previous_role: Mapped[str] = mapped_column(String(20), nullable=False)
    new_role: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CommunityOwnershipChange(Base):
    __tablename__ = "community_ownership_changes"
    __table_args__ = (
        CheckConstraint(
            "previous_owner_public_id <> new_owner_public_id",
            name="ck_community_ownership_changes_distinct_owners",
        ),
        Index(
            "ix_community_ownership_changes_community_transferred_at",
            "community_public_id",
            "transferred_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    community_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
    )
    community_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    previous_owner_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    previous_owner_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    new_owner_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    new_owner_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    transferred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CommunityLifecycleEvent(Base):
    __tablename__ = "community_lifecycle_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('archived', 'restored')",
            name="ck_community_lifecycle_events_event_type",
        ),
        Index(
            "ix_community_lifecycle_events_community_occurred_at",
            "community_public_id",
            "occurred_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    community_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
    )
    community_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_public_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CommunityInvite(Base):
    __tablename__ = "community_invites"
    __table_args__ = (
        CheckConstraint(
            "token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_community_invites_token_hash_sha256",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_community_invites_expiry_after_creation",
        ),
        CheckConstraint(
            "NOT (consumed_at IS NOT NULL AND revoked_at IS NOT NULL)",
            name="ck_community_invites_not_consumed_and_revoked",
        ),
        UniqueConstraint("public_id", name="uq_community_invites_public_id"),
        UniqueConstraint("token_hash", name="uq_community_invites_token_hash"),
        Index("ix_community_invites_community_id", "community_id"),
        Index("ix_community_invites_expires_at", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    public_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )
    community_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
