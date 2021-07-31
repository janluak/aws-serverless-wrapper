from aws_schema import SchemaValidator
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
        "requestContext": {
            "type": "object",
            "properties": {
                "authorizer": {
                    "claims": {
                        "auth_time": {
                            "type": "string",
                            "pattern": "^\\d*$"
                        },
                        "exp": {
                            "type": "string",
                            "pattern": "^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dez) (0[1-9]|[12]\d|3[01]) ([01]\d|2[0-4]):([0-5]\d|60):([0-5]\d|60) UTC (2[01]\d\d)$"
                        },
                        "sub": {
                            "type": "string",
                            "pattern": "^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$"
                        },
                        "iss": {
                            "type": "string",
                            "pattern": "^https:\/\/cognito-idp.\w\w-\w+-\d.amazonaws.com\/\w\w-\w+-\d_\S*$"
                        }
                    }
                }
            }
        },
        "multiValueQueryStringParameters": {
            "type": "object",
            "patternProperties": {
                "^[\\S]+$": {"type": "array"}
            },
        },
    },
}

__all__ = ["compose_ReST_event"]


def compose_ReST_event(
    httpMethod,
    resource,
    headers=None,
    body=None,
    pathParameters=None,
    queryParameters=None,
    requestContext=None,
    cognito_claims=None,
):
    if pathParameters is None:
        pathParameters = dict()

    event = {
        "resource": resource,
        "httpMethod": httpMethod,
        "headers": headers if headers else dict(),
        "path": resource.format(**pathParameters),
        "pathParameters": pathParameters,
        "multiValueQueryStringParameters": queryParameters
        if queryParameters
        else dict(),
        "requestContext": requestContext if requestContext else dict(),
    }

    if body is not None:
        casted_content_type = "text/plain"
        if isinstance(body, str):
            event.update({"body": body})
        elif isinstance(body, dict):
            event.update({"body": dumps(body)})
            casted_content_type = "application/json"

        if not any("content-type" == i.lower() for i in event["headers"]):
            event["headers"].update({"Content-Type": casted_content_type})
    
    if cognito_claims:
        if "authorizer" not in event["requestContext"]:
            event["requestContext"].update({"authorizer": {"claims": cognito_claims}})
        else:
            event["requestContext"]["authorizer"].update({"claims": cognito_claims})
            

    SchemaValidator(raw=__event_schema).validate(event)

    return event
