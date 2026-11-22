from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ontology.metamodel.enums import (
    ReleaseStatus,
    ValidationStatus,
    VersionState,
)
from ontology.metamodel.models import OntologyVersion, Release, ValidationRun
from ontology.metamodel.versioning import (
    ImmutableSnapshotError,
    assert_immutable_snapshot,
    assert_release_eligible,
    compute_snapshot_hash,
)


def test_snapshot_hash_is_deterministic():
    left = {"a": 1, "b": {"x": 2, "y": 3}}
    right = {"b": {"y": 3, "x": 2}, "a": 1}
    assert compute_snapshot_hash(left) == compute_snapshot_hash(right)


def test_immutable_snapshot_rejects_changed_content():
    snapshot = {"classes": [{"iri": "https://example.org/C"}]}
    recorded_hash = compute_snapshot_hash(snapshot)
    assert_immutable_snapshot(recorded_hash, snapshot)

    changed = {"classes": [{"iri": "https://example.org/Changed"}]}
    with pytest.raises(ImmutableSnapshotError):
        assert_immutable_snapshot(recorded_hash, changed)


def test_release_requires_validated_version_and_passed_validation():
    project_id = uuid4()
    ontology_id = uuid4()
    version_id = uuid4()
    validation_id = uuid4()
    user_id = uuid4()
    now = datetime.now(timezone.utc)

    version = OntologyVersion(
        id=version_id, project_id=project_id,
        created_at=now, updated_at=now,
        created_by=user_id, updated_by=user_id,
        ontology_id=ontology_id, version="1.0.0",
        state=VersionState.VALIDATED,
        snapshot_ref="s3://p1/snapshots/v1.json",
        snapshot_sha256="a" * 64,
    )
    validation = ValidationRun(
        id=validation_id, project_id=project_id,
        created_at=now, updated_at=now,
        created_by=user_id, updated_by=user_id,
        target_type="ontology_version", target_id=version_id,
        validator_name="p1-semantic-validator",
        validator_version="1.0.0", ruleset_version="1.0.0",
        status=ValidationStatus.PASSED,
    )
    release = Release(
        id=uuid4(), project_id=project_id,
        created_at=now, updated_at=now,
        created_by=user_id, updated_by=user_id,
        ontology_id=ontology_id, ontology_version_id=version_id,
        validation_run_id=validation_id,
        status=ReleaseStatus.PREPARING,
        artifact_ref="s3://p1/releases/v1.owl",
        artifact_sha256="b" * 64,
    )

    assert_release_eligible(version, validation, release)


def test_release_rejects_cross_project_validation():
    project_id = uuid4()
    ontology_id = uuid4()
    version_id = uuid4()
    now = datetime.now(timezone.utc)
    user_id = uuid4()

    version = OntologyVersion(
        id=version_id, project_id=project_id,
        created_at=now, updated_at=now,
        created_by=user_id, updated_by=user_id,
        ontology_id=ontology_id, version="1.0.0",
        state=VersionState.VALIDATED,
        snapshot_ref="snapshot.json",
        snapshot_sha256="a" * 64,
    )
    validation = ValidationRun(
        id=uuid4(), project_id=uuid4(),
        created_at=now, updated_at=now,
        created_by=user_id, updated_by=user_id,
        target_type="ontology_version", target_id=version_id,
        validator_name="validator", validator_version="1.0.0",
        ruleset_version="1.0.0", status=ValidationStatus.PASSED,
    )
    release = Release(
        id=uuid4(), project_id=project_id,
        created_at=now, updated_at=now,
        created_by=user_id, updated_by=user_id,
        ontology_id=ontology_id, ontology_version_id=version_id,
        validation_run_id=validation.id,
        status=ReleaseStatus.PREPARING,
        artifact_ref="release.owl", artifact_sha256="b" * 64,
    )

    with pytest.raises(ValueError):
        assert_release_eligible(version, validation, release)
