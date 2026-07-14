"""Small local validator for the self-contained Phase C1 output schema."""
from __future__ import annotations

import re
from typing import Any


class SchemaSubsetError(ValueError):
    pass


class SchemaCompatibilityError(ValueError):
    pass


def _is_json_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected) is True


def validate_schema_compatibility(schema: dict[str, Any], path: str = "$") -> None:
    """Validate the strict, non-recursive subset used by the C1 Codex fixture."""
    if not isinstance(schema, dict):
        raise SchemaCompatibilityError(f"{path} must be a schema object")
    allowed = {"$schema", "type", "required", "properties", "additionalProperties", "enum", "const", "pattern", "items", "anyOf"}
    unknown = sorted(set(schema) - allowed)
    if unknown:
        raise SchemaCompatibilityError(f"{path} uses unsupported keywords: {', '.join(unknown)}")
    unsupported = {
        "$ref", "$recursiveRef", "$dynamicRef", "$defs", "definitions", "oneOf", "allOf", "not",
        "if", "then", "else", "patternProperties", "unevaluatedProperties", "contains",
        "minContains", "maxContains", "uniqueItems", "minItems", "maxItems",
    }
    present_unsupported = sorted(unsupported.intersection(schema))
    if present_unsupported:
        raise SchemaCompatibilityError(f"{path} uses unsupported keywords: {', '.join(present_unsupported)}")
    expected = schema.get("type")
    if isinstance(expected, list):
        raise SchemaCompatibilityError(f"{path}.type must not be a union")
    if expected is not None and expected not in {"object", "array", "string", "integer", "number", "boolean", "null"}:
        raise SchemaCompatibilityError(f"{path}.type is unsupported: {expected}")
    if "enum" in schema:
        if expected is None:
            raise SchemaCompatibilityError(f"{path} enum requires an explicit type")
        if not isinstance(schema["enum"], list) or not schema["enum"]:
            raise SchemaCompatibilityError(f"{path}.enum must be a non-empty array")
        for index, value in enumerate(schema["enum"]):
            if isinstance(value, (list, dict)):
                raise SchemaCompatibilityError(f"{path}.enum[{index}] must not be array- or object-valued")
            if not _is_json_type(value, expected):
                raise SchemaCompatibilityError(f"{path}.enum[{index}] does not match type {expected}")
    if "const" in schema:
        if expected is None:
            raise SchemaCompatibilityError(f"{path} const requires an explicit type")
        if not _is_json_type(schema["const"], expected):
            raise SchemaCompatibilityError(f"{path}.const does not match type {expected}")
        if isinstance(schema["const"], (list, dict)):
            raise SchemaCompatibilityError(f"{path}.const must not be array- or object-valued")
    if expected == "object":
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            raise SchemaCompatibilityError(f"{path} object requires explicit properties")
        required = schema.get("required")
        if not isinstance(required, list):
            raise SchemaCompatibilityError(f"{path} object requires an explicit required array")
        if set(required) != set(properties):
            raise SchemaCompatibilityError(f"{path}.required must list every declared property exactly")
        if schema.get("additionalProperties") is not False:
            raise SchemaCompatibilityError(f"{path} object requires additionalProperties false")
        for name, child in properties.items():
            if not isinstance(child, dict) or "type" not in child:
                raise SchemaCompatibilityError(f"{path}.properties.{name} requires an explicit type")
            validate_schema_compatibility(child, f"{path}.properties.{name}")
    if expected == "array":
        items = schema.get("items")
        if isinstance(items, list):
            raise SchemaCompatibilityError(f"{path} tuple-style array items are unsupported")
        if not isinstance(items, dict):
            raise SchemaCompatibilityError(f"{path} array requires an explicit items schema")
        validate_schema_compatibility(items, f"{path}.items")
    if "anyOf" in schema:
        if path == "$":
            raise SchemaCompatibilityError("Root-level anyOf is unsupported")
        options = schema["anyOf"]
        if not isinstance(options, list) or not options:
            raise SchemaCompatibilityError(f"{path}.anyOf must be a non-empty array")
        for index, option in enumerate(options):
            if not isinstance(option, dict) or "type" not in option:
                raise SchemaCompatibilityError(f"{path}.anyOf[{index}] requires an explicit type")
            validate_schema_compatibility(option, f"{path}.anyOf[{index}]")


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "anyOf" in schema:
        failures = []
        for option in schema["anyOf"]:
            try:
                validate(instance, option, path)
                break
            except SchemaSubsetError as exc:
                failures.append(str(exc))
        else:
            raise SchemaSubsetError(f"{path} does not match any allowed schema")
    if "const" in schema and instance != schema["const"]:
        raise SchemaSubsetError(f"{path} does not equal required const")
    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaSubsetError(f"{path} is not in enum")
    expected = schema.get("type")
    if expected:
        if not _is_json_type(instance, expected):
            raise SchemaSubsetError(f"{path} is not type {expected}")
    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [name for name in required if name not in instance]
        if missing:
            raise SchemaSubsetError(f"{path} missing required fields: {', '.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(instance) - set(properties))
            if extras:
                raise SchemaSubsetError(f"{path} has extra fields: {', '.join(extras)}")
        for name, child_schema in properties.items():
            if name in instance:
                validate(instance[name], child_schema, f"{path}.{name}")
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < int(schema["minItems"]):
            raise SchemaSubsetError(f"{path} has too few items")
        if "maxItems" in schema and len(instance) > int(schema["maxItems"]):
            raise SchemaSubsetError(f"{path} has too many items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, value in enumerate(instance):
                validate(value, item_schema, f"{path}[{index}]")
    if isinstance(instance, str) and "pattern" in schema and not re.search(schema["pattern"], instance):
        raise SchemaSubsetError(f"{path} does not match required pattern")
