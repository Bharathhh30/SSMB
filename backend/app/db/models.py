"""Import all ORM models so Alembic sees their tables in ``Base.metadata``."""

from app.features.auth.models import (
    AuthActionToken,
    AuthRateLimitBucket,
    AuthRefreshToken,
    AuthSession,
)
from app.features.communities.models import (
    Community,
    CommunityInvite,
    CommunityLifecycleEvent,
    CommunityMembership,
    CommunityMetadataChange,
    CommunityOwnershipChange,
    CommunityRoleChange,
)
from app.features.profiles.models import UserInterest
from app.features.users.models import User

__all__ = [
    "AuthActionToken",
    "AuthRateLimitBucket",
    "AuthRefreshToken",
    "AuthSession",
    "Community",
    "CommunityInvite",
    "CommunityLifecycleEvent",
    "CommunityMetadataChange",
    "CommunityMembership",
    "CommunityOwnershipChange",
    "CommunityRoleChange",
    "User",
    "UserInterest",
]
