"""Import all ORM models so Alembic sees their tables in ``Base.metadata``."""

from app.features.auth.models import (
    AuthActionToken,
    AuthRateLimitBucket,
    AuthRefreshToken,
    AuthSession,
)
from app.features.communities.models import Community, CommunityMembership
from app.features.profiles.models import UserInterest
from app.features.users.models import User

__all__ = [
    "AuthActionToken",
    "AuthRateLimitBucket",
    "AuthRefreshToken",
    "AuthSession",
    "Community",
    "CommunityMembership",
    "User",
    "UserInterest",
]
