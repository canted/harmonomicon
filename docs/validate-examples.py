"""Validate bundled examples against their real JSON schemas; never run a host."""
import json
from pathlib import Path

from jsonschema.validators import validator_for

here = Path(__file__).resolve().parent
catalog = json.loads((here / "examples.json").read_text())
validators = {}
for entry in catalog:
    package = json.loads((here / entry["file"]).read_text())
    version = package["format"].removeprefix("harmonomicon.activity-package/")
    if version not in {"0.20", "0.21", "0.22", "0.23", "0.24"}:
        raise ValueError(f"Unsupported schema version: {version}")
    if version not in validators:
        schema = json.loads((here.parent / "format" / version / "package.schema.json").read_text())
        validator = validator_for(schema)
        validator.check_schema(schema)
        validators[version] = validator(schema)
    validators[version].validate(package)
print(f"Validated {len(catalog)} catalog packages against format {', '.join(validators)} JSON Schema.")
