"""Pydantic models for the P1 ontology platform meta-model."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from ontology.metamodel.enums import (
    ChangeOperation,
    ConstraintEngine,
    DataSourceType,
    DiscoveryJobStatus,
    EvidenceSourceType,
    FindingSeverity,
    LifecycleStatus,
    MappingStatus,
    MappingType,
    ProposalStatus,
    PropertyCharacteristic,
    ReleaseStatus,
    ValidationStatus,
    VersionState,
)
from ontology.metamodel.identifiers import (
    ensure_absolute_iri,
    normalize_language_tag,
    parse_semver,
)


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part[:1].upper() + part[1:] for part in rest)


class StrictModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        validate_assignment=True,
        use_enum_values=False,
    )


class ProjectScoped(StrictModel):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    extensions: dict[str, Any] = Field(default_factory=dict)


class Label(StrictModel):
    value: str = Field(min_length=1, max_length=500)
    language: str = Field(min_length=2, max_length=35)

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return normalize_language_tag(value)


class SourceReference(StrictModel):
    source_type: EvidenceSourceType
    source_id: str = Field(min_length=1)
    locator: str | None = None
    content_ref: str | None = None


class OntologyProject(StrictModel):
    id: UUID
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str | None = None
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    created_at: datetime
    updated_at: datetime


class Domain(ProjectScoped):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    parent_domain_id: UUID | None = None


class Ontology(ProjectScoped):
    domain_id: UUID
    name: str = Field(min_length=1, max_length=200)
    namespace: str
    description: str | None = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    current_version_id: UUID | None = None

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, value: str) -> str:
        return ensure_absolute_iri(value)


class OntologyVersion(ProjectScoped):
    ontology_id: UUID
    version: str
    schema_version: str = "1.0.0"
    state: VersionState = VersionState.DRAFT
    snapshot_ref: str = Field(min_length=1)
    snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("version", "schema_version")
    @classmethod
    def validate_versions(cls, value: str) -> str:
        parse_semver(value)
        return value


class OntologyClass(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str
    preferred_labels: list[Label] = Field(min_length=1)
    definition: str | None = None
    parent_class_ids: list[UUID] = Field(default_factory=list)
    abstract: bool = False
    status: LifecycleStatus = LifecycleStatus.DRAFT
    source_refs: list[SourceReference] = Field(default_factory=list)

    @field_validator("iri")
    @classmethod
    def validate_class_iri(cls, value: str) -> str:
        return ensure_absolute_iri(value)

    @field_validator("parent_class_ids")
    @classmethod
    def unique_parents(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("parent_class_ids must be unique.")
        return value


class DatatypeProperty(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str
    domain_class_ids: list[UUID] = Field(min_length=1)
    datatype_iri: str
    min_count: int | None = Field(default=None, ge=0)
    max_count: int | None = Field(default=None, ge=0)

    @field_validator("iri", "datatype_iri")
    @classmethod
    def validate_iris(cls, value: str) -> str:
        return ensure_absolute_iri(value)

    @field_validator("domain_class_ids")
    @classmethod
    def unique_domain_classes(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("domain_class_ids must be unique.")
        return value

    @model_validator(mode="after")
    def validate_cardinality(self):
        if (
            self.min_count is not None
            and self.max_count is not None
            and self.min_count > self.max_count
        ):
            raise ValueError("min_count cannot exceed max_count.")
        return self


class ObjectProperty(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str
    domain_class_ids: list[UUID] = Field(min_length=1)
    range_class_ids: list[UUID] = Field(min_length=1)
    inverse_property_id: UUID | None = None
    characteristics: list[PropertyCharacteristic] = Field(default_factory=list)

    @field_validator("iri")
    @classmethod
    def validate_property_iri(cls, value: str) -> str:
        return ensure_absolute_iri(value)

    @model_validator(mode="after")
    def unique_class_lists(self):
        if len(self.domain_class_ids) != len(set(self.domain_class_ids)):
            raise ValueError("domain_class_ids must be unique.")
        if len(self.range_class_ids) != len(set(self.range_class_ids)):
            raise ValueError("range_class_ids must be unique.")
        return self


class Relation(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    object_property_id: UUID
    source_class_id: UUID
    target_class_id: UUID
    display_label: str | None = None


class Constraint(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    target_type: str = Field(min_length=1)
    target_id: UUID
    engine: ConstraintEngine
    severity: FindingSeverity
    expression: str | None = None
    expression_ref: str | None = None

    @model_validator(mode="after")
    def exactly_one_expression_location(self):
        if bool(self.expression) == bool(self.expression_ref):
            raise ValueError("Provide exactly one of expression or expression_ref.")
        return self


class Term(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str | None = None
    preferred_labels: list[Label] = Field(min_length=1)
    definition: str | None = None

    @field_validator("iri")
    @classmethod
    def validate_term_iri(cls, value: str | None) -> str | None:
        return ensure_absolute_iri(value) if value is not None else None


class Alias(ProjectScoped):
    term_id: UUID
    label: str = Field(min_length=1, max_length=500)
    language: str = Field(min_length=2, max_length=35)
    alias_type: str = Field(min_length=1)

    @field_validator("language")
    @classmethod
    def normalize_alias_language(cls, value: str) -> str:
        return normalize_language_tag(value)


class DataSource(ProjectScoped):
    name: str = Field(min_length=1, max_length=200)
    source_type: DataSourceType
    connection_secret_ref: str = Field(min_length=1)
    configuration: dict[str, Any] = Field(default_factory=dict)
    status: LifecycleStatus = LifecycleStatus.ACTIVE

    @field_validator("connection_secret_ref")
    @classmethod
    def reject_inline_secret(cls, value: str) -> str:
        lowered = value.lower()
        if any(token in lowered for token in ("password=", "token=", "secret=")):
            raise ValueError("Store a secret reference, not an inline credential.")
        return value


class MetadataAsset(ProjectScoped):
    data_source_id: UUID
    asset_type: str = Field(min_length=1)
    qualified_name: str = Field(min_length=1)
    source_native_id: str | None = None
    metadata_snapshot_ref: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class DataMapping(ProjectScoped):
    source_asset_id: UUID
    target_element_id: UUID
    target_element_type: str = Field(min_length=1)
    mapping_type: MappingType
    status: MappingStatus = MappingStatus.PROPOSED
    evidence_ids: list[UUID] = Field(default_factory=list)
    expression_ref: str | None = None


class DiscoveryJob(ProjectScoped):
    ontology_id: UUID | None = None
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    status: DiscoveryJobStatus = DiscoveryJobStatus.QUEUED
    input_snapshot_ref: str = Field(min_length=1)
    configuration: dict[str, Any] = Field(default_factory=dict)


class DiscoveryProposal(ProjectScoped):
    discovery_job_id: UUID
    candidate_type: str = Field(min_length=1)
    payload: dict[str, Any]
    status: ProposalStatus = ProposalStatus.PENDING
    evidence_ids: list[UUID] = Field(default_factory=list)
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None


class Evidence(ProjectScoped):
    proposal_id: UUID
    source_type: EvidenceSourceType
    source_id: str = Field(min_length=1)
    location: str | None = None
    content_ref: str | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    excerpt: str | None = None


class ValidationRun(ProjectScoped):
    target_type: str = Field(min_length=1)
    target_id: UUID
    validator_name: str = Field(min_length=1)
    validator_version: str = Field(min_length=1)
    ruleset_version: str = Field(min_length=1)
    status: ValidationStatus = ValidationStatus.QUEUED
    summary: dict[str, int] = Field(default_factory=dict)
    report_ref: str | None = None


class Finding(ProjectScoped):
    validation_run_id: UUID
    rule_id: str = Field(min_length=1)
    severity: FindingSeverity
    message: str = Field(min_length=1)
    target_element_id: UUID | None = None
    details_ref: str | None = None


class ChangeRecord(ProjectScoped):
    ontology_id: UUID
    from_version_id: UUID | None = None
    to_version_id: UUID
    operation: ChangeOperation
    target_element_id: UUID
    diff_ref: str = Field(min_length=1)
    reason: str | None = None
    changed_by: UUID
    changed_at: datetime


class Release(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    validation_run_id: UUID
    status: ReleaseStatus = ReleaseStatus.PREPARING
    artifact_ref: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    published_at: datetime | None = None


class OntologyVersionSnapshot(StrictModel):
    """Portable immutable content snapshot for one ontology version."""

    id: UUID
    project_id: UUID
    ontology_id: UUID
    version: str
    schema_version: str = "1.0.0"
    namespace: str
    classes: list[OntologyClass] = Field(default_factory=list)
    datatype_properties: list[DatatypeProperty] = Field(default_factory=list)
    object_properties: list[ObjectProperty] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    terms: list[Term] = Field(default_factory=list)
    created_at: datetime

    @field_validator("version", "schema_version")
    @classmethod
    def validate_snapshot_versions(cls, value: str) -> str:
        parse_semver(value)
        return value

    @field_validator("namespace")
    @classmethod
    def validate_snapshot_namespace(cls, value: str) -> str:
        return ensure_absolute_iri(value)
