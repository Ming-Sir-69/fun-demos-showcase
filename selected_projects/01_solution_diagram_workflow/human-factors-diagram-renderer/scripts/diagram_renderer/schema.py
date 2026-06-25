"""DSL loading and schema-related helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


def load_dsl_from_json(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON DSL must be an object.")
    return data


def default_schema_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        for rel in (
            "references/diagram_dsl_v0_1_schema.json",
            "specs/diagram_dsl_v0_1_schema.json",
        ):
            candidate = parent / rel
            if candidate.exists():
                return candidate
    raise FileNotFoundError("Cannot locate diagram_dsl_v0_1_schema.json.")


def load_schema(path: str | Path | None = None) -> Dict[str, Any]:
    schema_path = Path(path) if path else default_schema_path()
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    if not isinstance(schema, dict):
        raise ValueError("JSON schema must be an object.")
    return schema


def validate_dsl_schema(dsl: Dict[str, Any], schema_path: str | Path | None = None) -> List[str]:
    schema = load_schema(schema_path)
    return _validate_schema_node(dsl, schema, schema, "$")


def _resolve_ref(ref: str, root_schema: Dict[str, Any]) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local JSON Schema refs are supported: {ref}")
    node: Any = root_schema
    for part in ref[2:].split("/"):
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"Schema ref does not resolve to an object: {ref}")
    return node


def _json_type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    return True


def _validate_schema_node(value: Any, schema: Dict[str, Any], root_schema: Dict[str, Any], path: str) -> List[str]:
    if "$ref" in schema:
        return _validate_schema_node(value, _resolve_ref(schema["$ref"], root_schema), root_schema, path)

    errors: List[str] = []

    if "allOf" in schema:
        for item in schema["allOf"]:
            errors.extend(_validate_schema_node(value, item, root_schema, path))

    if "if" in schema and "then" in schema:
        if not _validate_schema_node(value, schema["if"], root_schema, path):
            errors.extend(_validate_schema_node(value, schema["then"], root_schema, path))

    if "anyOf" in schema:
        branch_errors = [_validate_schema_node(value, item, root_schema, path) for item in schema["anyOf"]]
        if all(branch for branch in branch_errors):
            errors.append(f"{path}: must match at least one allowed schema branch.")

    if "not" in schema:
        if not _validate_schema_node(value, schema["not"], root_schema, path):
            errors.append(f"{path}: matches a forbidden schema branch.")

    if "type" in schema and not _json_type_ok(value, schema["type"]):
        errors.append(f"{path}: expected {schema['type']}, got {type(value).__name__}.")
        return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}.")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} is not in enum {schema['enum']!r}.")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required key {key!r}.")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            for key in extra:
                errors.append(f"{path}: additional property {key!r} is not allowed.")

        for key, child_schema in properties.items():
            if key in value:
                errors.extend(_validate_schema_node(value[key], child_schema, root_schema, f"{path}.{key}"))

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: expected at least {schema['minItems']} items.")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(_validate_schema_node(item, item_schema, root_schema, f"{path}[{index}]"))

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: expected length >= {schema['minLength']}.")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: expected length <= {schema['maxLength']}.")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}.")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: expected >= {schema['minimum']}.")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: expected <= {schema['maximum']}.")

    return errors
