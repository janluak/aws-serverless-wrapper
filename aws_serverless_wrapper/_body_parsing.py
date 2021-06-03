
__all__ = ["parse_body", "ParsingError"]


class ParsingError(ValueError):
    pass


def text_plain(data, _=None):
    if not isinstance(data, str):
        raise ParsingError(
            {
                "statusCode": 400,
                "body": "Body has to be plain text",
                "headers": {"Content-Type": "text/plain"},
            }
        )
    return data


def application_json(data, _=None):
    if isinstance(data, str):
        from json import loads, JSONDecodeError
        try:
            return loads(data)
        except (JSONDecodeError, TypeError):
            raise ParsingError(
                {
                    "statusCode": 400,
                    "body": "Body has to be json formatted",
                    "headers": {"Content-Type": "text/plain"},
                }
            )
    else:
        from json import dumps
        return dumps(data)


def application_x_www_form_urlencoded(data, encoding="utf-8"):
    try:
        if isinstance(data, str):
            from urllib.parse import parse_qs
            parsed = parse_qs(data, encoding=encoding)
            if not parsed and data:
                raise TypeError
            return parsed
        else:
            from urllib.parse import urlencode
            return urlencode(data, encoding=encoding)
    except TypeError:
        raise ParsingError(
            {
                "statusCode": 400,
                "body": "Body has to be x-www-form-urlencoded formatted",
                "headers": {"Content-Type": "text/plain"},
            }
        )


ContentTypeSwitch = {
    "text/plain": text_plain,
    "application/json": application_json,
    "application/x-www-form-urlencoded": application_x_www_form_urlencoded
}


def parse_body(event_or_response, encoding="utf-8"):
    if "body" not in event_or_response or event_or_response["body"] is None:
        return event_or_response

    if "headers" in event_or_response and "content-type" in event_or_response["headers"]:
        content_type = event_or_response["headers"]["content-type"]
    elif "headers" in event_or_response and "Content-Type" in event_or_response["headers"]:
        content_type = event_or_response["headers"]["Content-Type"]
    else:
        raise ParsingError("Content-Type must either be defined by header in event or by parameter")

    encoding = encoding.lower()
    try:
        event_or_response["body"] = ContentTypeSwitch[content_type](event_or_response["body"], encoding)
    except KeyError as KE:
        raise NotImplementedError(
            {
                "statusCode": 501,
                "body": f"parsing of Content-Type {KE} not implemented",
                "headers": {"Content-Type": "text/plain"}
            }
        )
    return event_or_response
