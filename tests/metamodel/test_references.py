from uuid import uuid4

from ontology.validators.reference_validator import ReferenceValidator


def make_snapshot():
    project_id = str(uuid4())
    ontology_id = str(uuid4())
    version_id = str(uuid4())
    class_a = str(uuid4())
    class_b = str(uuid4())
    object_property = str(uuid4())

    def scoped(object_id):
        return {
            "id": object_id,
            "projectId": project_id,
            "ontologyId": ontology_id,
            "ontologyVersionId": version_id,
        }

    return {
        "id": version_id,
        "projectId": project_id,
        "ontologyId": ontology_id,
        "classes": [
            {**scoped(class_a), "parentClassIds": []},
            {**scoped(class_b), "parentClassIds": [class_a]},
        ],
        "datatypeProperties": [],
        "objectProperties": [
            {
                **scoped(object_property),
                "domainClassIds": [class_a],
                "rangeClassIds": [class_b],
            }
        ],
        "relations": [
            {
                **scoped(str(uuid4())),
                "objectPropertyId": object_property,
                "sourceClassId": class_a,
                "targetClassId": class_b,
            }
        ],
        "constraints": [],
        "terms": [],
    }


def test_valid_snapshot_references_pass():
    issues = ReferenceValidator().validate_snapshot(make_snapshot())
    assert issues == ()


def test_unresolved_parent_is_reported():
    snapshot = make_snapshot()
    snapshot["classes"][1]["parentClassIds"] = [str(uuid4())]
    issues = ReferenceValidator().validate_snapshot(snapshot)
    assert any(issue.code == "UNRESOLVED_PARENT_CLASS" for issue in issues)


def test_relation_must_reference_existing_object_property():
    snapshot = make_snapshot()
    snapshot["relations"][0]["objectPropertyId"] = str(uuid4())
    issues = ReferenceValidator().validate_snapshot(snapshot)
    assert any(issue.code == "UNRESOLVED_OBJECT_PROPERTY" for issue in issues)
