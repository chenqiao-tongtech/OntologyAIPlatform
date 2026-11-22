from uuid import UUID

import pytest

from ontology.metamodel.identifiers import (
    compare_semver,
    ensure_absolute_iri,
    join_iri,
    new_id,
    normalize_language_tag,
    parse_id,
    parse_semver,
)


def test_internal_id_round_trip():
    value = new_id()
    assert isinstance(value, UUID)
    assert parse_id(str(value)) == value


def test_invalid_internal_id_is_rejected():
    with pytest.raises(ValueError):
        parse_id("not-a-uuid")


@pytest.mark.parametrize(
    "value",
    [
        "https://example.org/ontology#Customer",
        "urn:example:customer",
        "mailto:ontology@example.org",
    ],
)
def test_absolute_iri_is_accepted(value):
    assert ensure_absolute_iri(value) == value


@pytest.mark.parametrize(
    "value",
    ["Customer", "/relative/path", "https://", "https://bad host/example"],
)
def test_invalid_iri_is_rejected(value):
    with pytest.raises(ValueError):
        ensure_absolute_iri(value)


def test_join_iri_encodes_local_name():
    assert join_iri("https://example.org/ontology", "Customer Profile") == (
        "https://example.org/ontology#Customer%20Profile"
    )


def test_language_tag_normalization():
    assert normalize_language_tag("zh-cn") == "zh-CN"
    assert normalize_language_tag("en-us") == "en-US"


def test_semver_comparison():
    assert compare_semver("1.2.0", "1.1.9") == 1
    assert compare_semver("1.0.0-alpha", "1.0.0") == -1
    assert parse_semver("2.1.0")[0:3] == (2, 1, 0)
