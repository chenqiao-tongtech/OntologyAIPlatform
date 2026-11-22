//
//  ReleaseError.swift
//  
//
//  Created by joechen on 2026/11/22.
//



from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping, Protocol
from uuid import UUID, uuid4

from ontology.versioning.models import (
    Artifact,
    ReleaseRecord,
    ReleaseStatus,
    VersionRecord,
    VersionStatus,
)


class ReleaseError(RuntimeError):
    pass


class ActiveVersionConflict(ReleaseError):
    pass


class ReleaseAuthorizationError(ReleaseError):
    pass


@dataclass(frozen=True)
class BuiltArtifact:
    format: str
    content: bytes
    media_type: str


class ArtifactBuilder(Protocol):
    def build(
        self,
        version: VersionRecord,
        formats: tuple[str, ...],
    ) -> tuple[BuiltArtifact, ...]:
        ...


class ImmutableArtifactStore(Protocol):
    def put_if_absent(
        self,
        key: str,
        content: bytes,
        media_type: str,
    ) -> str:
        """Store content immutably and return its storage reference."""
        ...


class ReleaseAuthorization(Protocol):
    def authorize(
        self,
        actor_id: UUID,
        permission: str,
        project_id: UUID,
    ) -> None:
        ...


class ReleaseVersionRepository(Protocol):
    def get(self, version_id: UUID) -> VersionRecord: ...


class ReleaseUnitOfWork(Protocol):
    def find_by_idempotency_key(
        self,
        key: str,
    ) -> ReleaseRecord | None:
        ...

    def get_active_version(
        self,
        ontology_id: UUID,
        environment: str,
    ) -> UUID | None:
        ...

    def create_release(self, release: ReleaseRecord) -> ReleaseRecord:
        ...

    def set_active_version(
        self,
        ontology_id: UUID,
        environment: str,
        new_version_id: UUID,
        expected_old_version_id: UUID | None,
    ) -> None:
        ...

    def add_outbox_event(
        self,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> None:
        ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> AbstractContextManager[ReleaseUnitOfWork]:
        ...


class ReleaseAttemptRepository(Protocol):
    def record_failure(
        self,
        attempt_id: UUID,
        error: str,
    ) -> None:
        ...


class ReleaseService:
    def __init__(
        self,
        versions: ReleaseVersionRepository,
        builder: ArtifactBuilder,
        artifact_store: ImmutableArtifactStore,
        uow_factory: UnitOfWorkFactory,
        authorization: ReleaseAuthorization,
        attempts: ReleaseAttemptRepository,
    ):
        self.versions = versions
        self.builder = builder
        self.artifact_store = artifact_store
        self.uow_factory = uow_factory
        self.authorization = authorization
        self.attempts = attempts

    def publish(
        self,
        version_id: UUID,
        environment: str,
        actor_id: UUID,
        idempotency_key: str,
        expected_active_version_id: UUID | None,
        formats: tuple[str, ...] = ("turtle", "rdfxml"),
        rollback_of_release_id: UUID | None = None,
    ) -> ReleaseRecord:
        if not idempotency_key.strip():
            raise ValueError("An idempotency key is required.")

        version = self.versions.get(version_id)

        permission = (
            "release.rollback"
            if rollback_of_release_id is not None
            else "release.publish"
        )
        self.authorization.authorize(
            actor_id,
            permission,
            version.project_id,
        )

        # A formal version must already be validated.
        if version.status not in {
            VersionStatus.VALIDATED,
            VersionStatus.PUBLISHED,
        }:
            raise ReleaseError(
                "Only a validated or previously published version can be released."
            )

        # Fast idempotency check. A unique DB constraint remains mandatory.
        with self.uow_factory() as uow:
            existing = uow.find_by_idempotency_key(idempotency_key)
            if existing is not None:
                if (
                    existing.version_id != version_id
                    or existing.environment != environment
                ):
                    raise ReleaseError(
                        "Idempotency key was already used with a different payload."
                    )
                return existing

        attempt_id = uuid4()

        try:
            built = self.builder.build(version, formats)
            if not built:
                raise ReleaseError("Artifact builder returned no artifacts.")

            artifacts: list[Artifact] = []

            for item in built:
                if not item.content:
                    raise ReleaseError(
                        f"Empty release artifact: {item.format}"
                    )

                digest = sha256(item.content).hexdigest()
                key = (
                    f"releases/{version.ontology_id}/"
                    f"{version.id}/{digest}.{item.format}"
                )

                storage_ref = self.artifact_store.put_if_absent(
                    key,
                    item.content,
                    item.media_type,
                )

                artifacts.append(
                    Artifact(
                        format=item.format,
                        storage_ref=storage_ref,
                        sha256=digest,
                        media_type=item.media_type,
                    )
                )

            release = ReleaseRecord(
                id=uuid4(),
                project_id=version.project_id,
                ontology_id=version.ontology_id,
                version_id=version.id,
                environment=environment,
                status=ReleaseStatus.PUBLISHED,
                artifacts=tuple(artifacts),
                idempotency_key=idempotency_key,
                published_by=actor_id,
                published_at=datetime.now(timezone.utc),
                rollback_of_release_id=rollback_of_release_id,
            )

            # Commit Release + active pointer + Outbox atomically in the DB.
            with self.uow_factory() as uow:
                existing = uow.find_by_idempotency_key(idempotency_key)
                if existing is not None:
                    if (
                        existing.version_id != version_id
                        or existing.environment != environment
                    ):
                        raise ReleaseError(
                            "Idempotency key was reused with another payload."
                        )
                    return existing

                actual_active = uow.get_active_version(
                    version.ontology_id,
                    environment,
                )
                if actual_active != expected_active_version_id:
                    raise ActiveVersionConflict(
                        "The active version changed during publication. "
                        "Reload the release plan and retry."
                    )

                created = uow.create_release(release)

                uow.set_active_version(
                    ontology_id=version.ontology_id,
                    environment=environment,
                    new_version_id=version.id,
                    expected_old_version_id=expected_active_version_id,
                )

                uow.add_outbox_event(
                    "ontology.release.published",
                    {
                        "releaseId": str(created.id),
                        "ontologyId": str(created.ontology_id),
                        "versionId": str(created.version_id),
                        "environment": created.environment,
                        "rollbackOfReleaseId": (
                            str(created.rollback_of_release_id)
                            if created.rollback_of_release_id else None
                        ),
                    },
                )

                return created

        except Exception as exc:
            # Active pointer is unchanged if the DB transaction did not commit.
            # Uploaded immutable objects may remain orphaned and are cleaned
            # by a retention-based garbage collector.
            self.attempts.record_failure(
                attempt_id,
                f"{type(exc).__name__}: {exc}",
            )
            raise
