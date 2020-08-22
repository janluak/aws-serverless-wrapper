from ..schema_validation import SchemaValidator
from json import dumps

__event_schema = {
    "title": "AWS Event Schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "additionalProperties": False,
    "properties": {
        "resource": {"type": "string", "pattern": "^/[\\S]+$"},
        "httpMethod": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
        "headers": {"type": "object"},
        "path": {"type": "string"},
        "body": {"type": "string"},
        "pathParameters": {"type": "object"},
        "requestContext": {"type": "object"},
        "multiValueQueryStringParameters": {
            "type": "object",
            "patternProperties": {
                "^[\\S]+$": {"type": "array", "items": {"type": "string"}}
            },
        },
    },
}

__all__ = ["compose_ReST_event"]


def compose_ReST_event(
    httpMethod,
    resource,
    header=None,
    body=None,
    pathParameters=None,
    queryParameters=None,
    requestContext=None,
):
    if pathParameters is None:
        pathParameters = dict()

    event = {
        "resource": resource,
        "httpMethod": httpMethod,
        "headers": header if header else dict(),
        "path": resource.format(**pathParameters),
        "pathParameters": pathParameters,
        "multiValueQueryStringParameters": queryParameters
        if queryParameters
        else dict(),
        "requestContext": requestContext if requestContext else dict(),
    }
    if isinstance(body, str):
        event.update({"body": body})
        event["headers"].update({"Content-Type": "text/plain"})
    elif isinstance(body, dict):
        event.update({"body": dumps(body)})
        event["headers"].update({"Content-Type": "application/json"})

    SchemaValidator(raw=__event_schema).validate(event)

    return event
