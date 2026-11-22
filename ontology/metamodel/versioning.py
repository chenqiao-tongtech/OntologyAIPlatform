"""Immutable ontology snapshot hashing and release eligibility checks."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from pydantic import BaseModel

from ontology.metamodel.enums import ValidationStatus, VersionState
from ontology.metamodel.models import OntologyVersion, Release, ValidationRun


class ImmutableSnapshotError(ValueError):
    pass


class ReleaseEligibilityError(ValueError):
    pass


def _json_compatible(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_none=False)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    return value


def canonical_json(value: Any) -> str:
    """Serialize deterministic JSON for content hashing."""
    compatible = _json_compatible(value)
    return json.dumps(
        compatible,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def compute_snapshot_hash(snapshot: Any) -> str:
    return hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()


def assert_immutable_snapshot(
    existing_sha256: str,
    candidate_snapshot: Any,
) -> None:
    """Raise when a supposedly immutable version's content has changed."""
    candidate_hash = compute_snapshot_hash(candidate_snapshot)
    if candidate_hash != existing_sha256:
        raise ImmutableSnapshotError(
            "Immutable ontology version content does not match its recorded hash."
        )


def assert_release_eligible(
    version: OntologyVersion,
    validation_run: ValidationRun,
    release: Release,
) -> None:
    """Check project, version and validation links before publication."""
    if version.state != VersionState.VALIDATED:
        raise ReleaseEligibilityError("Only validated ontology versions can be released.")
    if validation_run.status != ValidationStatus.PASSED:
        raise ReleaseEligibilityError("Release requires a passed validation run.")
    if version.project_id != validation_run.project_id:
        raise ReleaseEligibilityError("Version and validation run projects differ.")
    if version.project_id != release.project_id:
        raise ReleaseEligibilityError("Version and release projects differ.")
    if release.ontology_id != version.ontology_id:
        raise ReleaseEligibilityError("Release references a different ontology.")
    if release.ontology_version_id != version.id:
        raise ReleaseEligibilityError("Release must reference the exact ontology version.")
    if release.validation_run_id != validation_run.id:
        raise ReleaseEligibilityError("Release references a different validation run.")
