# P1 Ontology Meta-model V1.0

This package contains the P1 ontology platform meta-model baseline:

- Pydantic models and controlled enums
- Identifier and IRI helpers
- Typed internal/external references
- JSON Schema Draft 2020-12 documents
- Schema, reference, semantic and compatibility validators
- Immutable snapshot hashing and release eligibility checks
- Unit tests and architecture documentation

## Runtime

- Python 3.11+
- Pydantic 2.x
- jsonschema 4.x
- referencing 0.35+

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

On Windows, activate with `.venv\\Scripts\\activate`.

## Test

```bash
pytest tests/metamodel -v
```

## Validate a schema

```python
from pathlib import Path
from ontology.validators.schema_validator import SchemaValidator

validator = SchemaValidator(Path("ontology/schemas"))
report = validator.validate(
    {"id": "not-a-uuid"},
    "project",
)
print(report.valid, report.issues)
```

## Important boundaries

- JSON Schema validates object shape; it does not validate database references.
- ReferenceValidator enforces snapshot-local reference and project boundaries.
- SemanticValidator checks selected internal ontology invariants.
- SHACL and OWL adapters are separate integration tasks; this package does not claim to implement them.
- Published version immutability must also be enforced transactionally by the persistence layer.
- Credentials are represented by secret references; the application must integrate a real secret manager.

This is an engineering baseline, not a claim that the complete P1 platform is deployed or production-certified.
