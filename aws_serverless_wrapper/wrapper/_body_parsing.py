
__all__ = ["parse_body"]


def text_plain(data):
    if not isinstance(data, str):
        raise TypeError(
            {
                "statusCode": 400,
                "body": "Body has to be plain text",
                "headers": {"Content-Type": "text/plain"},
            }
        )
    return data


def application_json(data):
    if isinstance(data, str):
        from json import loads, JSONDecodeError
        try:
            return loads(data)
        except (JSONDecodeError, TypeError):
            raise TypeError(
                {
                    "statusCode": 400,
                    "body": "Body has to be json formatted",
                    "headers": {"Content-Type": "text/plain"},
                }
            )
    else:
        from json import dumps
        return dumps(data)


def content_type_switch(content_type: str):
    if content_type == "text/plain":
        return text_plain
    elif content_type == "application/json":
        return application_json


def parse_body(event_or_response):
    if "body" not in event_or_response or not event_or_response["body"]:
        return event_or_response

    content_type = None
    if "headers" in event_or_response and "content-type" in event_or_response["headers"]:
        content_type = event_or_response["headers"]["content-type"]
    elif "headers" in event_or_response and "Content-Type" in event_or_response["headers"]:
        content_type = event_or_response["headers"]["Content-Type"]

    if content_type is None:
        raise ValueError("Content-Type must either be defined by header in event or by parameter")

    event_or_response["body"] = content_type_switch(content_type)(event_or_response["body"])
    return event_or_response
