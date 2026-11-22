//
//  import.swift
//  
//
//  Created by joechen on 2026/11/22.
//



from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"


class CandidateStatus(str, Enum):
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    VALIDATION_FAILED = "validation_failed"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    VERSION_CREATED = "version_created"


class VersionStatus(str, Enum):
    VALIDATED = "validated"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class ReleaseStatus(str, Enum):
    PREPARING = "preparing"
    ARTIFACTS_READY = "artifacts_ready"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"


class Compatibility(str, Enum):
    COMPATIBLE = "compatible"
    CONDITIONALLY_COMPATIBLE = "conditionally_compatible"
    BREAKING = "breaking"
    UNKNOWN = "unknown"


class ImpactLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Workspace:
    id: UUID
    project_id: UUID
    ontology_id: UUID
    name: str
    base_version_id: UUID | None
    base_snapshot_hash: str | None
    head_revision: int
    status: WorkspaceStatus
    owner_id: UUID


@dataclass(frozen=True)
class WorkspaceRevision:
    id: UUID
    workspace_id: UUID
    revision: int
    snapshot_ref: str
    snapshot_hash: str
    author_id: UUID
    created_at: datetime


@dataclass(frozen=True)
class CandidateSubmission:
    id: UUID
    project_id: UUID
    ontology_id: UUID
    workspace_id: UUID
    revision_id: UUID
    base_version_id: UUID | None
    snapshot_ref: str
    snapshot_hash: str
    status: CandidateStatus
    submitted_by: UUID
    submitted_at: datetime
    diff_ref: str | None = None
    validation_run_id: UUID | None = None
    approval_record_id: UUID | None = None


@dataclass(frozen=True)
class VersionRecord:
    id: UUID
    project_id: UUID
    ontology_id: UUID
    version: str
    schema_version: str
    parent_version_id: UUID | None
    candidate_id: UUID
    snapshot_ref: str
    snapshot_hash: str
    status: VersionStatus
    created_by: UUID
    created_at: datetime


@dataclass(frozen=True)
class ApprovalRecord:
    id: UUID
    candidate_id: UUID
    decision: str
    reviewer_id: UUID
    comment: str | None
    decided_at: datetime


@dataclass(frozen=True)
class Artifact:
    format: str
    storage_ref: str
    sha256: str
    media_type: str


@dataclass(frozen=True)
class ReleaseRecord:
    id: UUID
    project_id: UUID
    ontology_id: UUID
    version_id: UUID
    environment: str
    status: ReleaseStatus
    artifacts: tuple[Artifact, ...]
    idempotency_key: str
    published_by: UUID
    published_at: datetime | None = None
    rollback_of_release_id: UUID | None = None


@dataclass(frozen=True)
class SemanticChange:
    change_type: str
    target_type: str
    target_id: str | None
    target_iri: str | None
    impact: ImpactLevel
    compatibility: Compatibility
    migration_required: bool
    rationale: str
    old_value: Any = None
    new_value: Any = None


@dataclass(frozen=True)
class SemanticDiffReport:
    source_version: str | None
    target_version: str | None
    changes: tuple[SemanticChange, ...]
    generated_at: datetime = field(default_factory=utc_now)

    @property
    def has_breaking_changes(self) -> bool:
        return any(
            change.compatibility == Compatibility.BREAKING
            for change in self.changes
        )

    @property
    def has_unknown_changes(self) -> bool:
        return any(
            change.compatibility == Compatibility.UNKNOWN
            for change in self.changes
        )
