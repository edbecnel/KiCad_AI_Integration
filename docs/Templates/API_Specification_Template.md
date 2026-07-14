# [API Name] Specification

## Status

**Required**

Draft | In Review | Approved | Implemented | Deprecated

## Purpose

**Required**

Describe the API's responsibility and intended consumers.

## Scope

**Required**

### In Scope

- [Capability]

### Out of Scope

- [Capability]

## Base Information

**Required**

- Base path or endpoint:
- Protocol:
- Data format:
- Versioning strategy:

## Authentication and Authorization

**Required**

Describe credentials, tokens, roles, permissions, and failure behavior.

## Common Conventions

**Required**

Describe identifiers, timestamps, pagination, filtering, sorting, idempotency, and naming conventions.

## Endpoints

### [METHOD] [Path]

**Purpose**

[Description]

**Authorization**

[Requirement]

**Path Parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| [name] | [type] | Yes/No | [description] |

**Query Parameters**

| Name | Type | Required | Description |
|---|---|---:|---|
| [name] | [type] | Yes/No | [description] |

**Request Body**

```json
{
  "example": "value"
}
```

**Successful Response**

- Status: `[code]`

```json
{
  "example": "value"
}
```

**Error Responses**

| Status | Code | Meaning |
|---:|---|---|
| [status] | [code] | [meaning] |

## Validation Rules

**Required**

- [Rule]

## Error Model

**Required**

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": []
  }
}
```

## Rate Limiting

**Optional**

[Policy]

## Security Considerations

**Required**

- [Consideration]

## Compatibility and Deprecation

**Optional**

[Policy]

## Testing

**Required**

- Contract tests:
- Authentication tests:
- Validation tests:
- Error-path tests:

## References

**Optional**

- [Related document]
