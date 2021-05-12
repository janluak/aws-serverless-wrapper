
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


ContentTypeSwitch = {
    "text/plain": text_plain,
    "application/json": application_json
}


def parse_body(event_or_response):
    if "body" not in event_or_response or event_or_response["body"] is None:
        return event_or_response

    if "headers" in event_or_response and "content-type" in event_or_response["headers"]:
        content_type = event_or_response["headers"]["content-type"]
    elif "headers" in event_or_response and "Content-Type" in event_or_response["headers"]:
        content_type = event_or_response["headers"]["Content-Type"]
    else:
        raise ValueError("Content-Type must either be defined by header in event or by parameter")

    try:
        event_or_response["body"] = ContentTypeSwitch[content_type](event_or_response["body"])
    except KeyError as KE:
        raise NotImplementedError(
            {
                "statusCode": 501,
                "body": f"parsing of Content-Type {KE} not implemented",
                "headers": {"Content-Type": "text/plain"}
            }
        )
    return event_or_response
