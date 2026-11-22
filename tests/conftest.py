from pathlib import Path

import pytest

from ontology.validators.schema_validator import SchemaValidator


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def schema_dir():
    return ROOT / "ontology" / "schemas"


@pytest.fixture(scope="session")
def schema_validator(schema_dir):
    return SchemaValidator(schema_dir)


@pytest.fixture
def valid_class_payload():
    from uuid import uuid4
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "id": str(uuid4()),
        "projectId": str(uuid4()),
        "ontologyId": str(uuid4()),
        "ontologyVersionId": str(uuid4()),
        "createdAt": now,
        "updatedAt": now,
        "createdBy": str(uuid4()),
        "updatedBy": str(uuid4()),
        "iri": "https://example.org/customer#Customer",
        "preferredLabels": [{"value": "Customer", "language": "en"}],
        "definition": "A person or organization that purchases goods or services.",
        "parentClassIds": [],
        "abstract": False,
        "status": "draft",
        "sourceRefs": [],
        "extensions": {}
    }
