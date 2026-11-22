//
//  import.swift
//  
//
//  Created by joechen on 2026/11/21.
//



from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class LifecycleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class DiscoveryStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class ValidationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReleaseStatus(str, Enum):
    PREPARING = "preparing"
    PUBLISHED = "published"
    WITHDRAWN = "withdrawn"


class ProjectScoped(StrictModel):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    extensions: dict[str, Any] = Field(default_factory=dict)


class OntologyProject(StrictModel):
    id: UUID
    name: str
    description: str | None = None
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    created_at: datetime
    updated_at: datetime


class Domain(ProjectScoped):
    name: str
    description: str | None = None
    parent_domain_id: UUID | None = None


class Ontology(ProjectScoped):
    domain_id: UUID
    name: str
    namespace: str
    description: str | None = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    current_version_id: UUID | None = None


class OntologyVersion(ProjectScoped):
    ontology_id: UUID
    version: str
    schema_version: str
    snapshot_ref: str
    snapshot_sha256: str
    state: str


class Label(StrictModel):
    value: str = Field(min_length=1)
    language: str = Field(min_length=2)


class SourceReference(StrictModel):
    type: str
    id: str


class OntologyClass(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str = Field(min_length=1)
    preferred_labels: list[Label] = Field(min_length=1)
    definition: str | None = None
    parent_class_ids: list[UUID] = Field(default_factory=list)
    abstract: bool = False
    status: LifecycleStatus = LifecycleStatus.DRAFT
    source_refs: list[SourceReference] = Field(default_factory=list)


class DatatypeProperty(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str
    domain_class_ids: list[UUID] = Field(min_length=1)
    datatype_iri: str
    min_count: int | None = Field(default=None, ge=0)
    max_count: int | None = Field(default=None, ge=0)


class ObjectProperty(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str
    domain_class_ids: list[UUID] = Field(min_length=1)
    range_class_ids: list[UUID] = Field(min_length=1)
    inverse_property_id: UUID | None = None
    characteristics: list[str] = Field(default_factory=list)


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
    target_element_id: UUID
    engine: str
    severity: str
    payload_ref: str


class Term(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    iri: str | None = None
    preferred_labels: list[Label] = Field(min_length=1)
    definition: str | None = None


class Alias(ProjectScoped):
    term_id: UUID
    label: str
    language: str
    alias_type: str


class DataSource(ProjectScoped):
    name: str
    source_type: str
    connection_secret_ref: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE


class MetadataAsset(ProjectScoped):
    data_source_id: UUID
    asset_type: str
    qualified_name: str
    source_native_id: str | None = None
    metadata_snapshot_ref: str | None = None


class DataMapping(ProjectScoped):
    source_asset_id: UUID
    target_element_id: UUID
    target_element_type: str
    mapping_type: str
    status: str
    evidence_ids: list[UUID] = Field(default_factory=list)


class DiscoveryJob(ProjectScoped):
    ontology_id: UUID | None = None
    provider_id: str
    provider_version: str
    status: DiscoveryStatus
    input_snapshot_ref: str
    configuration: dict[str, Any] = Field(default_factory=dict)


class DiscoveryProposal(ProjectScoped):
    discovery_job_id: UUID
    candidate_type: str
    payload: dict[str, Any]
    status: ProposalStatus = ProposalStatus.PENDING
    evidence_ids: list[UUID] = Field(default_factory=list)


class Evidence(ProjectScoped):
    proposal_id: UUID
    source_asset_id: UUID | None = None
    source_ref: str
    location: str | None = None
    content_ref: str | None = None
    content_sha256: str | None = None


class ValidationRun(ProjectScoped):
    ontology_version_id: UUID
    validator_name: str
    validator_version: str
    ruleset_version: str
    status: ValidationStatus


class Finding(ProjectScoped):
    validation_run_id: UUID
    rule_id: str
    severity: str
    message: str
    target_element_id: UUID | None = None
    details_ref: str | None = None


class ChangeRecord(ProjectScoped):
    ontology_id: UUID
    from_version_id: UUID | None = None
    to_version_id: UUID
    operation: str
    target_element_id: UUID
    diff_ref: str
    changed_by: UUID
    changed_at: datetime


class Release(ProjectScoped):
    ontology_id: UUID
    ontology_version_id: UUID
    validation_run_id: UUID
    status: ReleaseStatus
    artifact_ref: str
    published_at: datetime | None = None
