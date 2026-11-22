# P1 JSON Schemas

- Dialect: JSON Schema Draft 2020-12
- All `$ref` resources are registered locally by `ontology.validators.SchemaValidator`.
- No remote schema retrieval is performed.
- `property.schema.json` accepts either a DatatypeProperty or an ObjectProperty.
- `ontology-version.schema.json` describes the portable version snapshot artifact.
- Database metadata records (`OntologyVersion`) and immutable snapshot artifacts
  (`OntologyVersionSnapshot`) are distinct concepts.
