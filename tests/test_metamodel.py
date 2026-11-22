#
//  test_metamodel.py
//  
//
//  Created by joechen on 2026/11/21.
//



from datetime import datetime, timezone
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from ontology.metamodel.models import (
    Label,
    OntologyClass,
    ObjectProperty,
)
from ontology.metamodel.validators import (
    MetaModelReferenceError,
    validate_class_references,
    validate_object_property_references,
)


def make_class(project_id, class_id=None, parent_ids=None):
    now = datetime.now(timezone.utc)

    return OntologyClass(
        id=class_id or uuid4(),
        project_id=project_id,
        ontology_id=uuid4(),
        ontology_version_id=uuid4(),
        created_at=now,
        updated_at=now,
        created_by=uuid4(),
        updated_by=uuid4(),
        iri=f"https://example.org/test#{uuid4().hex}",
        preferred_labels=[Label(value="Test", language="en")],
        parent_class_ids=parent_ids or [],
    )


def test_class_schema_validates_valid_payload(class_schema):
    validator = Draft202012Validator(
        class_schema,
        format_checker=FormatChecker(),
    )

    payload = {
        "id": str(uuid4()),
        "projectId": str(uuid4()),
        "ontologyVersionId": str(uuid4()),
        "iri": "https://example.org/customer#Customer",
        "preferredLabels": [
            {"value": "Customer", "language": "en"}
        ],
        "parentClassIds": [],
        "status": "draft"
    }

    assert list(validator.iter_errors(payload)) == []


def test_class_schema_rejects_missing_required_field(class_schema):
    validator = Draft202012Validator(
        class_schema,
        format_checker=FormatChecker(),
    )

    payload = {
        "id": str(uuid4()),
        "projectId": str(uuid4())
    }

    errors = list(validator.iter_errors(payload))
    assert errors


def test_class_id_is_stable_after_rename():
    project_id = uuid4()
    item = make_class(project_id)
    original_id = item.id

    renamed = item.model_copy(
        update={
            "preferred_labels": [
                Label(value="Client", language="en")
            ]
        }
    )

    assert renamed.id == original_id


def test_parent_reference_must_exist():
    project_id = uuid4()
    parent = make_class(project_id)
    child = make_class(
        project_id,
        parent_ids=[parent.id],
    )

    validate_class_references(
        project_id,
        [parent, child],
    )


def test_missing_parent_reference_is_rejected():
    project_id = uuid4()
    child = make_class(
        project_id,
        parent_ids=[uuid4()],
    )

    with pytest.raises(MetaModelReferenceError):
        validate_class_references(
            project_id,
            [child],
        )


def test_cross_project_class_reference_is_rejected():
    project_a = uuid4()
    project_b = uuid4()

    item_a = make_class(project_a)
    item_b = make_class(
        project_b,
        parent_ids=[item_a.id],
    )

    with pytest.raises(MetaModelReferenceError):
        validate_class_references(
            project_b,
            [item_a, item_b],
        )


def test_object_property_domain_and_range_must_exist():
    project_id = uuid4()
    domain = make_class(project_id)
    range_class = make_class(project_id)

    now = datetime.now(timezone.utc)

    prop = ObjectProperty(
        id=uuid4(),
        project_id=project_id,
        ontology_id=uuid4(),
        ontology_version_id=uuid4(),
        created_at=now,
        updated_at=now,
        created_by=uuid4(),
        updated_by=uuid4(),
        iri="https://example.org/test#hasOrder",
        domain_class_ids=[domain.id],
        range_class_ids=[range_class.id],
    )

    validate_object_property_references(
        project_id,
        [domain, range_class],
        [prop],
    )
