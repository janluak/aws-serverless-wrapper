from pytest import raises


def test_simple_json_event():
    from aws_serverless_wrapper.testing import compose_ReST_event

    expected_event = {
        "body": '{"abc": "def"}',
        "headers": {"Content-Type": "application/json"},
        "httpMethod": "POST",
        "multiValueQueryStringParameters": {},
        "path": "/api_name",
        "pathParameters": {},
        "requestContext": {},
        "resource": "/api_name",
    }
    composed_event = compose_ReST_event(
        httpMethod="POST", resource="/api_name", body={"abc": "def"}
    )

    assert composed_event == expected_event


def test_simple_string_body_event():
    from aws_serverless_wrapper.testing import compose_ReST_event

    expected_event = {
        "body": "abc def ghi",
        "headers": {"Content-Type": "text/plain"},
        "httpMethod": "POST",
        "multiValueQueryStringParameters": {},
        "path": "/api_name",
        "pathParameters": {},
        "requestContext": {},
        "resource": "/api_name",
    }
    composed_event = compose_ReST_event(
        httpMethod="POST", resource="/api_name", body="abc def ghi"
    )

    assert composed_event == expected_event


def test_variable_path_event():
    from aws_serverless_wrapper.testing import compose_ReST_event

    expected_event = {
        "body": '{"abc": "def"}',
        "headers": {"Content-Type": "application/json"},
        "httpMethod": "POST",
        "multiValueQueryStringParameters": {},
        "path": "/api_name/value1",
        "pathParameters": {"variable1": "value1"},
        "requestContext": {},
        "resource": "/api_name/{variable1}",
    }

    with raises(KeyError):
        compose_ReST_event(
            httpMethod="POST", resource="/api_name/{variable1}", body={"abc": "def"}
        )

    composed_event = compose_ReST_event(
        httpMethod="POST",
        resource="/api_name/{variable1}",
        pathParameters={"variable1": "value1"},
        body={"abc": "def"},
    )

    assert composed_event == expected_event
