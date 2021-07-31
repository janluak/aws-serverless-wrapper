from pytest import raises, mark


def test_event_without_body():
    from aws_serverless_wrapper.testing import compose_ReST_event

    expected_event = {
        "httpMethod": "GET",
        "path": "/api_name",
        "headers": dict(),
        "multiValueQueryStringParameters": dict(),
        "pathParameters": dict(),
        "requestContext": dict(),
        "resource": "/api_name",
    }
    composed_event = compose_ReST_event(
        "GET",
        "/api_name"
    )
    assert composed_event == expected_event


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


@mark.parametrize(
    "ct",
    ("content-type", "Content-Type")
)
def test_string_body_event_with_specified_headers(ct):
    from aws_serverless_wrapper.testing import compose_ReST_event

    expected_event = {
        "body": "abc=def",
        "headers": {ct: "application/x-www-form-urlencoded"},
        "httpMethod": "POST",
        "multiValueQueryStringParameters": {},
        "path": "/api_name",
        "pathParameters": {},
        "requestContext": {},
        "resource": "/api_name",
    }
    composed_event = compose_ReST_event(
        httpMethod="POST",
        resource="/api_name",
        body="abc=def",
        headers={ct: "application/x-www-form-urlencoded"}
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


def test_cognito_auth_event():
    from aws_serverless_wrapper.testing import compose_ReST_event

    expected_event = {
        "body": '{"abc": "def"}',
        "headers": {
            "Content-Type": "application/json",
        },
        "httpMethod": "POST",
        "multiValueQueryStringParameters": {},
        "path": "/api_name/value1",
        "pathParameters": {"variable1": "value1"},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "email": "some_mail@test.com",
                    "auth_time": "1615730814",
                    "exp": "Sun Mar 14 15:06:54 UTC 2021"
                }
            }
        },
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
        cognito_claims={
            "sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "email": "some_mail@test.com",
            "auth_time": "1615730814",
            "exp": "Sun Mar 14 15:06:54 UTC 2021"
        }
    )

    assert composed_event == expected_event
