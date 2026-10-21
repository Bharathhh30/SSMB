import re

from app.features.communities.service import _slugify, _with_unique_suffix


def test_slugify_is_url_safe_and_respects_database_length_after_normalization() -> None:
    slug = _slugify("\ufb03" * 120)

    assert len(slug) <= 140
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)


def test_slugify_uses_fallback_when_name_has_no_ascii_letters_or_digits() -> None:
    assert _slugify("🌱📚") == "community"


def test_unique_slug_suffix_remains_within_database_limit() -> None:
    slug = _with_unique_suffix("a" * 140)

    assert len(slug) == 140
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
