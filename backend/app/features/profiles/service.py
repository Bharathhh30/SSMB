from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.dependencies import AuthenticatedPrincipal
from app.features.profiles.models import UserInterest
from app.features.profiles.schemas import ProfileRead, ProfileUpdate


async def get_own_profile(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
) -> ProfileRead:
    user = principal.user
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

    if "interests" in update.model_fields_set:
        await session.execute(delete(UserInterest).where(UserInterest.user_id == user.id))
        session.add_all(
            [
                UserInterest(
                    user_id=user.id,
                    interest=interest,
                    normalized_interest=interest.casefold(),
                    position=position,
                )
                for position, interest in enumerate(update.interests or [])
            ]
        )

    await session.commit()
    await session.refresh(user)
    return await get_own_profile(session, principal)
