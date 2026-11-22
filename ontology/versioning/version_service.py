//
//  VersionServiceError.swift
//  
//
//  Created by joechen on 2026/11/22.
//



from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

from ontology.versioning.models import (
    ApprovalRecord,
    CandidateStatus,
    CandidateSubmission,
    VersionRecord,
    VersionStatus,
    Workspace,
    WorkspaceRevision,
    WorkspaceStatus,
)
from ontology.versioning.semantic_diff import SemanticDiffService
from ontology.versioning.snapshot import (
    compute_snapshot_hash,
    verify_snapshot_hash,
)


class VersionServiceError(RuntimeError):
    pass


class RevisionConflictError(VersionServiceError):
    pass


class CandidateStateError(VersionServiceError):
    pass


class SnapshotIntegrityError(VersionServiceError):
    pass


class WorkspaceRepository(Protocol):
    def get(self, workspace_id: UUID) -> Workspace: ...
    def get_revision(
        self,
        workspace_id: UUID,
        revision: int,
    ) -> WorkspaceRevision: ...

    def create_candidate(
        self,
        candidate: CandidateSubmission,
    ) -> CandidateSubmission: ...

    def get_candidate(
        self,
        candidate_id: UUID,
    ) -> CandidateSubmission: ...

    def update_candidate(
        self,
        candidate: CandidateSubmission,
    ) -> CandidateSubmission: ...


class SnapshotStore(Protocol):
    def get_json(self, reference: str) -> dict[str, Any]: ...

    def put_immutable_json(
        self,
        key: str,
        payload: dict[str, Any],
    ) -> str: ...


class VersionRepository(Protocol):
    def get_snapshot(
        self,
        version_id: UUID,
    ) -> dict[str, Any]: ...

    def create_if_absent(
        self,
        version: VersionRecord,
    ) -> VersionRecord: ...

    def find_by_candidate(
        self,
        candidate_id: UUID,
    ) -> VersionRecord | None: ...


class ValidationRepository(Protocol):
    def is_passed_for_snapshot(
        self,
        validation_run_id: UUID,
        snapshot_hash: str,
    ) -> bool: ...


class ApprovalRepository(Protocol):
    def get_approved_record(
        self,
        candidate_id: UUID,
        approval_record_id: UUID,
    ) -> ApprovalRecord: ...


class AuthorizationService(Protocol):
    def authorize(
        self,
        actor_id: UUID,
        permission: str,
        project_id: UUID,
    ) -> None: ...


class VersionService:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        version_repository: VersionRepository,
        snapshot_store: SnapshotStore,
        validation_repository: ValidationRepository,
        approval_repository: ApprovalRepository,
        authorization: AuthorizationService,
        diff_service: SemanticDiffService | None = None,
    ):
        self.workspaces = workspace_repository
        self.versions = version_repository
        self.snapshots = snapshot_store
        self.validations = validation_repository
        self.approvals = approval_repository
        self.authorization = authorization
        self.diff = diff_service or SemanticDiffService()

    def submit_candidate(
        self,
        workspace_id: UUID,
        actor_id: UUID,
        expected_revision: int,
    ) -> CandidateSubmission:
        workspace = self.workspaces.get(workspace_id)

        self.authorization.authorize(
            actor_id,
            "candidate.submit",
            workspace.project_id,
        )

        if workspace.status != WorkspaceStatus.ACTIVE:
            raise CandidateStateError("Workspace is not active.")

        if workspace.head_revision != expected_revision:
            raise RevisionConflictError(
                "Workspace changed since it was last loaded. "
                "Reload or rebase before submitting."
            )

        revision = self.workspaces.get_revision(
            workspace_id,
            expected_revision,
        )

        snapshot = self.snapshots.get_json(revision.snapshot_ref)
        actual_hash = compute_snapshot_hash(snapshot)

        if actual_hash != revision.snapshot_hash:
            raise SnapshotIntegrityError(
                "Workspace revision snapshot hash does not match."
            )

        diff_ref = None
        if workspace.base_version_id is not None:
            base_snapshot = self.versions.get_snapshot(
                workspace.base_version_id
            )
            diff_report = self.diff.compare(
                base_snapshot,
                snapshot,
            )
            # A production implementation stores the report immutably
            # and persists its reference here.
            diff_ref = None

        candidate_snapshot_ref = self.snapshots.put_immutable_json(
            key=f"candidates/{uuid4()}/{actual_hash}.json",
            payload=snapshot,
        )

        candidate = CandidateSubmission(
            id=uuid4(),
            project_id=workspace.project_id,
            ontology_id=workspace.ontology_id,
            workspace_id=workspace.id,
            revision_id=revision.id,
            base_version_id=workspace.base_version_id,
            snapshot_ref=candidate_snapshot_ref,
            snapshot_hash=actual_hash,
            status=CandidateStatus.SUBMITTED,
            submitted_by=actor_id,
            submitted_at=datetime.now(timezone.utc),
            diff_ref=diff_ref,
        )

        return self.workspaces.create_candidate(candidate)

    def mark_validation_result(
        self,
        candidate_id: UUID,
        validation_run_id: UUID,
        actor_id: UUID,
    ) -> CandidateSubmission:
        candidate = self.workspaces.get_candidate(candidate_id)

        self.authorization.authorize(
            actor_id,
            "candidate.validate",
            candidate.project_id,
        )

        if candidate.status not in {
            CandidateStatus.SUBMITTED,
            CandidateStatus.VALIDATING,
        }:
            raise CandidateStateError(
                f"Candidate cannot be validated from {candidate.status.value}."
            )

        passed = self.validations.is_passed_for_snapshot(
            validation_run_id,
            candidate.snapshot_hash,
        )

        new_status = (
            CandidateStatus.AWAITING_REVIEW
            if passed
            else CandidateStatus.VALIDATION_FAILED
        )

        updated = CandidateSubmission(
            **{
                **candidate.__dict__,
                "status": new_status,
                "validation_run_id": validation_run_id,
            }
        )
        return self.workspaces.update_candidate(updated)

    def create_version(
        self,
        candidate_id: UUID,
        version: str,
        schema_version: str,
        validation_run_id: UUID,
        approval_record_id: UUID,
        actor_id: UUID,
    ) -> VersionRecord:
        candidate = self.workspaces.get_candidate(candidate_id)

        self.authorization.authorize(
            actor_id,
            "version.create",
            candidate.project_id,
        )

        # Idempotency: one approved candidate maps to one formal version.
        existing = self.versions.find_by_candidate(candidate_id)
        if existing is not None:
            if existing.snapshot_hash != candidate.snapshot_hash:
                raise SnapshotIntegrityError(
                    "Existing version does not match candidate snapshot."
                )
            return existing

        if candidate.status != CandidateStatus.APPROVED:
            raise CandidateStateError(
                "Only an approved candidate can become a formal version."
            )

        if candidate.validation_run_id != validation_run_id:
            raise CandidateStateError(
                "Validation run does not belong to this candidate."
            )

        if not self.validations.is_passed_for_snapshot(
            validation_run_id,
            candidate.snapshot_hash,
        ):
            raise CandidateStateError(
                "Candidate has no passed validation for its frozen snapshot."
            )

        approval = self.approvals.get_approved_record(
            candidate_id,
            approval_record_id,
        )
        if approval.decision != "approved":
            raise CandidateStateError("Approval record is not approved.")

        if approval.reviewer_id == candidate.submitted_by:
            raise CandidateStateError(
                "Submitter cannot approve their own candidate under "
                "the configured separation-of-duties policy."
            )

        snapshot = self.snapshots.get_json(candidate.snapshot_ref)
        if not verify_snapshot_hash(snapshot, candidate.snapshot_hash):
            raise SnapshotIntegrityError(
                "Candidate snapshot content has changed."
            )

        version_record = VersionRecord(
            id=uuid4(),
            project_id=candidate.project_id,
            ontology_id=candidate.ontology_id,
            version=version,
            schema_version=schema_version,
            parent_version_id=candidate.base_version_id,
            candidate_id=candidate.id,
            snapshot_ref=candidate.snapshot_ref,
            snapshot_hash=candidate.snapshot_hash,
            status=VersionStatus.VALIDATED,
            created_by=actor_id,
            created_at=datetime.now(timezone.utc),
        )

        created = self.versions.create_if_absent(version_record)

        updated_candidate = CandidateSubmission(
            **{
                **candidate.__dict__,
                "status": CandidateStatus.VERSION_CREATED,
                "approval_record_id": approval_record_id,
            }
        )
        self.workspaces.update_candidate(updated_candidate)

        return created


def record_review_decision(
    self,
    candidate_id: UUID,
    approval_record_id: UUID,
    reviewer_id: UUID,
    approved: bool,
) -> CandidateSubmission:
    candidate = self.workspaces.get_candidate(candidate_id)

    self.authorization.authorize(
        reviewer_id,
        "candidate.review",
        candidate.project_id,
    )

    if candidate.status != CandidateStatus.AWAITING_REVIEW:
        raise CandidateStateError(
            "Only candidates awaiting review can be reviewed."
        )

    approval = self.approvals.get_approved_record(
        candidate_id,
        approval_record_id,
    )

    if approval.reviewer_id != reviewer_id:
        raise CandidateStateError(
            "Approval record reviewer does not match the current user."
        )

    if approved and approval.decision != "approved":
        raise CandidateStateError("Approval record is not approved.")

    if not approved and approval.decision != "rejected":
        raise CandidateStateError("Approval record is not rejected.")

    new_status = (
        CandidateStatus.APPROVED
        if approved
        else CandidateStatus.REJECTED
    )

    updated = CandidateSubmission(
        **{
            **candidate.__dict__,
            "status": new_status,
            "approval_record_id": approval_record_id,
        }
    )

    return self.workspaces.update_candidate(updated)
