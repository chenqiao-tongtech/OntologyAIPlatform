"""Typed references and project-boundary helpers."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology.metamodel.enums import ReferenceObjectType
from ontology.metamodel.identifiers import ensure_absolute_iri


class InternalReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["internal"] = "internal"
    object_type: ReferenceObjectType
    object_id: UUID
    project_id: UUID
    ontology_version_id: UUID | None = None


class ExternalReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["external"] = "external"
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    iri: str | None = None

    @model_validator(mode="after")
    def validate_iri(self):
        if self.iri is not None:
            ensure_absolute_iri(self.iri)
        return self


def assert_same_project(
    owner_project_id: UUID,
    target_project_id: UUID,
    *,
    allow_shared_asset: bool = False,
) -> None:
    """Reject cross-project internal references unless explicitly authorized."""
    if owner_project_id != target_project_id and not allow_shared_asset:
        raise ValueError("Cross-project internal reference is not allowed.")
