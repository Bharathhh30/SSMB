from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.dependencies import AuthenticatedPrincipal
from app.features.profiles.models import UserInterest
from app.features.profiles.schemas import ProfileRead, ProfileUpdate
from app.features.users.models import User

MAX_PROFILE_INTERESTS = 20


class ProfilePolicyError(ValueError):
    """Raised when a profile update would violate profile limits."""


async def get_own_profile(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
) -> ProfileRead:
    user = await session.scalar(select(User).where(User.id == principal.user.id).with_for_update())
    if user is None:
        raise ProfilePolicyError("The account is no longer available")

    interest_rows = await session.scalars(
        select(UserInterest)
        .where(UserInterest.user_id == user.id)
        .order_by(UserInterest.position.asc())
    )
    return ProfileRead(
        id=user.id,
        display_name=user.display_name or "",
        interests=[row.interest for row in interest_rows.all()],
    )


async def update_own_profile(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
    update: ProfileUpdate,
) -> ProfileRead:
    user = principal.user
    if "display_name" in update.model_fields_set:
        user.display_name = update.display_name

    if "interests" in update.model_fields_set or "remove_interests" in update.model_fields_set:
        current_rows = await session.scalars(
            select(UserInterest)
            .where(UserInterest.user_id == user.id)
            .order_by(UserInterest.position.asc())
        )
        current = {row.normalized_interest: row.interest for row in current_rows.all()}
        removals = {interest.casefold() for interest in update.remove_interests or []}
        additions = update.interests or []

        for normalized_interest in removals:
            current.pop(normalized_interest, None)
        for interest in additions:
            current.setdefault(interest.casefold(), interest)

        if len(current) > MAX_PROFILE_INTERESTS:
            raise ProfilePolicyError(
                f"A profile can have at most {MAX_PROFILE_INTERESTS} interests"
            )

        await session.execute(delete(UserInterest).where(UserInterest.user_id == user.id))
        session.add_all(
            [
                UserInterest(
                    user_id=user.id,
                    interest=interest,
                    normalized_interest=normalized,
                    position=position,
                )
                for position, (normalized, interest) in enumerate(current.items())
            ]
        )

    await session.commit()
    await session.refresh(user)
    return await get_own_profile(session, principal)
