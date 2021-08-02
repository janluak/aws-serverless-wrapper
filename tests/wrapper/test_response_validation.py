from aws_serverless_wrapper.testing import fake_context, compose_ReST_event
from os.path import dirname, realpath
from os import chdir, getcwd
from pytest import fixture
from freezegun import freeze_time
from aws_serverless_wrapper._environ_variables import environ
from json import loads


def response_test(event):
    return {
        "statusCode": event["body"]["response_statusCode"],
        "body": event["body"]["response_body"],
        "headers": {
            "Content-Type": "application/json"
            if isinstance(event["body"]["response_body"], dict)
            else "text/plain"
        },
    }


@fixture
def response_validation_env():
    actual_cwd = getcwd()
    chdir(dirname(realpath(__file__)))
    environ._load_config_from_file("api_response_wrapper_config.json")
    yield
    chdir(actual_cwd)


def test_200_single_string(response_validation_env, caplog):
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_response_resource",
        body={"response_statusCode": 200, "response_body": "single_allowed_answer"},
    )

    expected_response = {
        "statusCode": 200,
        "body": "single_allowed_answer",
        "headers": {"Content-Type": "text/plain"},
    }
    response = LambdaHandlerOfFunction(response_test).wrap_lambda(event, fake_context)
    assert response == expected_response
    assert len(caplog.messages) == 0


def test_200_false_single_string(response_validation_env, caplog):
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_response_resource",
        body={"response_statusCode": 200, "response_body": "not_allowed_answer"},
    )

    expected_response = {
        "statusCode": 200,
        "body": "not_allowed_answer",
        "headers": {"Content-Type": "text/plain"},
    }
    response = LambdaHandlerOfFunction(response_test).wrap_lambda(event, fake_context)
    assert response == expected_response
    assert len(caplog.messages) == 1
    assert "invalid response" in caplog.text


def test_unspecified_status_code_response(response_validation_env, caplog):
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_response_resource",
        body={"response_statusCode": 418, "response_body": "I'm a teapot"},
    )

    expected_response = {
        "statusCode": 418,
        "body": "I'm a teapot",
        "headers": {"Content-Type": "text/plain"},
    }
    response = LambdaHandlerOfFunction(response_test).wrap_lambda(event, fake_context)
    assert response == expected_response
    assert len(caplog.messages) == 1
    assert "no specified response schema available for statusCode 418" in caplog.text


def test_200_single_string_with_internal_server_error_configured(
    response_validation_env, caplog
):
    environ["API_RESPONSE_VERIFICATION"]["RETURN_INTERNAL_SERVER_ERROR"] = True
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_response_resource",
        body={"response_statusCode": 200, "response_body": "single_allowed_answer"},
    )

    expected_response = {
        "statusCode": 200,
        "body": "single_allowed_answer",
        "headers": {"Content-Type": "text/plain"},
    }
    response = LambdaHandlerOfFunction(response_test).wrap_lambda(event, fake_context)
    assert response == expected_response
    assert len(caplog.messages) == 0


@freeze_time("2020-01-01")
def test_200_false_single_string_with_internal_server_error(
    response_validation_env, caplog
):
    environ["API_RESPONSE_VERIFICATION"]["RETURN_INTERNAL_SERVER_ERROR"] = True
    environ["ERROR_LOG"] = {"API_RESPONSE": True}
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_response_resource",
        body={"response_statusCode": 200, "response_body": "not_allowed_answer"},
    )

    expected_response = {
        "body": {
            "error": {
                    "invalid response": {
                        "body": "not_allowed_answer",
                        "headers": {"Content-Type": "text/plain"},
                        "statusCode": 200,
                    },
                    "schema context": "[<ValidationError: "
                    "\"'not_allowed_answer' "
                    "is not one of "
                    "['single_allowed_answer']\">, "
                    "<ValidationError: "
                    "\"'not_allowed_answer' "
                    "is not of type "
                    "'object'\">]",
                },
            "error_log": {
                "aws_log_group": "test/log/group",
                "aws_request_id": "uuid",
                "function_version": "$LATEST",
                "lambda_name": "test_function",
                "service_name": "group",
                "statusCode": 500,
                "timestamp": 1577836800.0,
            },
        },
        "headers": {"Content-Type": "application/json"},
        "statusCode": 500,
    }
    response = LambdaHandlerOfFunction(response_test).wrap_lambda(event, fake_context)
    response["body"] = loads(response["body"])
    assert response == expected_response
    assert len(caplog.messages) == 1
    assert "invalid response" in caplog.text

