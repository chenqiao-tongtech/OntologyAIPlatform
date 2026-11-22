import json

from jsonschema import Draft202012Validator


def test_all_schema_documents_are_valid(schema_validator):
    assert len(schema_validator.list_schemas()) >= 20
    for name in schema_validator.list_schemas():
        schema_validator.check_schema(name)


def test_valid_class_payload_passes(schema_validator, valid_class_payload):
    report = schema_validator.validate(valid_class_payload, "class")
    assert report.valid, report.issues


def test_invalid_class_payload_fails(schema_validator, valid_class_payload):
    payload = dict(valid_class_payload)
    payload.pop("iri")
    report = schema_validator.validate(payload, "class")
    assert not report.valid
    assert any("iri" in issue.message.lower() or "required" in issue.message.lower()
               for issue in report.issues)


def test_property_schema_accepts_datatype_property(schema_validator):
    from uuid import uuid4
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "id": str(uuid4()), "projectId": str(uuid4()),
        "ontologyId": str(uuid4()), "ontologyVersionId": str(uuid4()),
        "createdAt": now, "updatedAt": now,
        "createdBy": str(uuid4()), "updatedBy": str(uuid4()),
        "iri": "https://example.org/customer#customerId",
        "domainClassIds": [str(uuid4())],
        "datatypeIri": "http://www.w3.org/2001/XMLSchema#string"
    }
    report = schema_validator.validate(payload, "property")
    assert report.valid, report.issues


def test_constraint_requires_exactly_one_expression_location(schema_validator):
    from uuid import uuid4
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "id": str(uuid4()), "projectId": str(uuid4()),
        "ontologyId": str(uuid4()), "ontologyVersionId": str(uuid4()),
        "createdAt": now, "updatedAt": now,
        "createdBy": str(uuid4()), "updatedBy": str(uuid4()),
        "targetType": "class", "targetId": str(uuid4()),
        "engine": "internal", "severity": "error",
        "expression": "must-have-label",
        "expressionRef": "s3://bucket/rule.json"
    }
    assert not schema_validator.validate(payload, "constraint").valid
