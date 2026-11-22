"""Controlled vocabulary for P1 meta-model objects."""

from enum import Enum


class StrEnum(str, Enum):
    """String enum compatible with Python 3.11+."""


class LifecycleStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class VersionState(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DiscoveryJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class ValidationStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReleaseStatus(StrEnum):
    PREPARING = "preparing"
    PUBLISHED = "published"
    WITHDRAWN = "withdrawn"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConstraintEngine(StrEnum):
    INTERNAL = "internal"
    JSON_SCHEMA = "json_schema"
    SHACL = "shacl"
    OWL = "owl"


class PropertyCharacteristic(StrEnum):
    FUNCTIONAL = "functional"
    INVERSE_FUNCTIONAL = "inverseFunctional"
    TRANSITIVE = "transitive"
    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    REFLEXIVE = "reflexive"
    IRREFLEXIVE = "irreflexive"


class DataSourceType(StrEnum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQL_SERVER = "sql_server"
    ORACLE = "oracle"
    MONGODB = "mongodb"
    DOCUMENT_STORE = "document_store"
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    GIT = "git"
    S3 = "s3"
    OTHER = "other"


class MappingType(StrEnum):
    EXACT = "exact"
    TRANSFORM = "transform"
    SEMANTIC = "semantic"
    CANDIDATE = "candidate"


class MappingStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class EvidenceSourceType(StrEnum):
    DATABASE_METADATA = "database_metadata"
    API_SCHEMA = "api_schema"
    DOCUMENT = "document"
    CODE = "code"
    USER_INPUT = "user_input"
    EXTERNAL_IRI = "external_iri"
    MODEL_OUTPUT = "model_output"


class ChangeOperation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    DEPRECATE = "deprecate"
    REPLACE = "replace"
    RENAME = "rename"


class ReferenceObjectType(StrEnum):
    PROJECT = "project"
    DOMAIN = "domain"
    ONTOLOGY = "ontology"
    ONTOLOGY_VERSION = "ontology_version"
    CLASS = "class"
    DATATYPE_PROPERTY = "datatype_property"
    OBJECT_PROPERTY = "object_property"
    RELATION = "relation"
    CONSTRAINT = "constraint"
    TERM = "term"
    DATA_SOURCE = "data_source"
    METADATA_ASSET = "metadata_asset"
    DATA_MAPPING = "data_mapping"
    DISCOVERY_JOB = "discovery_job"
    DISCOVERY_PROPOSAL = "discovery_proposal"
    EVIDENCE = "evidence"
    VALIDATION_RUN = "validation_run"
    FINDING = "finding"
    CHANGE_RECORD = "change_record"
    RELEASE = "release"
