import re
from uuid import UUID

from app.features.communities.service import _community_slug, _slugify


def test_slugify_is_url_safe_and_respects_database_length_after_normalization() -> None:
    slug = _slugify("\ufb03" * 120)

    assert len(slug) <= 107
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)


def test_slugify_uses_fallback_when_name_has_no_ascii_letters_or_digits() -> None:
    assert _slugify("🌱📚") == "community"


def test_community_slug_always_includes_its_stable_full_uuid() -> None:
    public_id = UUID("9e72456e-2d0e-47d3-8d15-64c7c8555c92")
    slug = _community_slug("GATE Study Circle", public_id)

    assert slug == f"gate-study-circle-{public_id.hex}"
    assert len(slug) <= 140
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
