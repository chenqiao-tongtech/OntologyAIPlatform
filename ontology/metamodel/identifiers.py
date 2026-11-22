"""Identifier and IRI helpers.

Internal UUIDs, semantic IRIs and source-native identifiers are different
identifier domains and must not be interchanged.
"""

from __future__ import annotations

import re
from urllib.parse import quote, urlsplit
from uuid import UUID, uuid4


_LANGUAGE_TAG_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_CONTROL_OR_SPACE_RE = re.compile(r"[\x00-\x20\x7f]")
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)


def new_id() -> UUID:
    """Create a new stable internal identifier."""
    return uuid4()


def parse_id(value: UUID | str) -> UUID:
    """Parse an internal UUID, raising ValueError for invalid input."""
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid UUID identifier: {value!r}") from exc


def ensure_absolute_iri(value: str) -> str:
    """Validate and return an absolute IRI-like identifier.

    This intentionally accepts non-HTTP schemes such as urn: as well as
    HTTP(S) IRIs. It rejects whitespace/control characters and malformed
    HTTP(S) authorities. Full Unicode normalization is left to the IRI
    parser/adapter used for a specific interchange format.
    """
    if not isinstance(value, str) or not value:
        raise ValueError("IRI must be a non-empty string.")
    if _CONTROL_OR_SPACE_RE.search(value) or "\\" in value:
        raise ValueError("IRI must not contain whitespace, control characters or backslashes.")
    if not _SCHEME_RE.match(value):
        raise ValueError(f"IRI must be absolute: {value!r}")

    try:
        parts = urlsplit(value)
    except ValueError as exc:
        raise ValueError(f"Malformed IRI: {value!r}") from exc

    if not parts.scheme:
        raise ValueError(f"IRI must be absolute: {value!r}")
    if parts.scheme.lower() in {"http", "https"} and not parts.netloc:
        raise ValueError("HTTP(S) IRI must include an authority.")
    if parts.netloc and " " in parts.netloc:
        raise ValueError("IRI authority contains invalid whitespace.")
    return value


def join_iri(namespace: str, local_name: str) -> str:
    """Append an encoded local name to a namespace."""
    ensure_absolute_iri(namespace)
    if not isinstance(local_name, str) or not local_name.strip():
        raise ValueError("Local IRI name must be a non-empty string.")
    if any(ord(char) < 32 or ord(char) == 127 for char in local_name):
        raise ValueError("Local IRI name must not contain control characters.")
    # Spaces are permitted in the supplied local name because quote() below
    # percent-encodes them. Control characters remain invalid.
    if re.search(r"[\\x00-\\x1f\\x7f]", local_name):
        raise ValueError("Local IRI name must not contain control characters.")
    base = namespace if namespace.endswith(("#", "/")) else namespace + "#"
    result = base + quote(local_name, safe="-._~")
    return ensure_absolute_iri(result)


def normalize_language_tag(value: str) -> str:
    """Normalize a practical BCP 47 language-tag subset.

    Language is lower-case, script is title-case, region is upper-case;
    remaining subtags are lower-case. Validation is intentionally
    conservative and does not replace a full BCP 47 registry lookup.
    """
    if not isinstance(value, str) or not _LANGUAGE_TAG_RE.fullmatch(value):
        raise ValueError(f"Invalid language tag: {value!r}")

    parts = value.split("-")
    normalized = [parts[0].lower()]
    for part in parts[1:]:
        if len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        elif (len(part) == 2 and part.isalpha()) or (len(part) == 3 and part.isdigit()):
            normalized.append(part.upper())
        else:
            normalized.append(part.lower())
    return "-".join(normalized)


def parse_semver(value: str) -> tuple[int, int, int, str | None, str | None]:
    """Parse a semantic version string."""
    match = _SEMVER_RE.fullmatch(value or "")
    if not match:
        raise ValueError(f"Invalid semantic version: {value!r}")
    major, minor, patch, prerelease, build = match.groups()
    return int(major), int(minor), int(patch), prerelease, build


def compare_semver(left: str, right: str) -> int:
    """Compare semantic versions. Build metadata does not affect precedence."""
    l_major, l_minor, l_patch, l_pre, _ = parse_semver(left)
    r_major, r_minor, r_patch, r_pre, _ = parse_semver(right)
    l_core = (l_major, l_minor, l_patch)
    r_core = (r_major, r_minor, r_patch)
    if l_core != r_core:
        return -1 if l_core < r_core else 1
    if l_pre == r_pre:
        return 0
    if l_pre is None:
        return 1
    if r_pre is None:
        return -1

    # Sufficient for migration ordering: compare prerelease identifiers.
    l_parts = l_pre.split(".")
    r_parts = r_pre.split(".")
    for l_item, r_item in zip(l_parts, r_parts):
        if l_item == r_item:
            continue
        l_num, r_num = l_item.isdigit(), r_item.isdigit()
        if l_num and r_num:
            return -1 if int(l_item) < int(r_item) else 1
        if l_num != r_num:
            return -1 if l_num else 1
        return -1 if l_item < r_item else 1
    if len(l_parts) == len(r_parts):
        return 0
    return -1 if len(l_parts) < len(r_parts) else 1
