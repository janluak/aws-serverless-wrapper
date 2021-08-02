import logging
from os.path import dirname, realpath
from os import chdir, getcwd
from freezegun import freeze_time
from pytest import fixture, mark, raises
from fil_io.json import load_single
from aws_serverless_wrapper._environ_variables import environ
from aws_serverless_wrapper import ServerlessBaseClass
from aws_serverless_wrapper.testing import fake_context as context, compose_ReST_event
from json import loads, dumps


def api_basic(event):
    pass


class RaiseExpectedException(ServerlessBaseClass):
    api_name = "api_basic"

    def main(self):
        raise FileNotFoundError(
            {
                "statusCode": 404,
                "body": "item in db not found",
                "headers": {"Content-Type": "text/plain"},
            }
        )


class RaiseUnexpectedException(ServerlessBaseClass):
    api_name = "api_basic"

    def main(self):
        raise Exception("some unexpected exception")


@fixture
def run_from_file_directory():
    actual_cwd = getcwd()
    chdir(dirname(realpath(__file__)))
    yield
    chdir(actual_cwd)


def test_wrong_method(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = {"httpMethod": "WRONG", "resource": "/test_request_resource"}

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)

    assert response == {
        "statusCode": 501,
        "body": "API is not defined",
        "headers": {"Content-Type": "text/plain"},
    }


@freeze_time("2020-01-01")
def test_wrong_method_with_error_response(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    environ["API_INPUT_VERIFICATION"]["LOG_ERRORS"]["API_RESPONSE"] = True

    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = {"httpMethod": "WRONG", "resource": "/test_request_resource"}

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)
    response["body"] = loads(response["body"])
    assert response == {
        "statusCode": 501,
        "body": {
            "error": "API is not defined",
            "error_log": {
                "lambda_name": "test_function",
                "service_name": "group",
                "function_version": "$LATEST",
                "headers": {"Content-Type": "text/plain"},
                "aws_log_group": "test/log/group",
                "aws_request_id": "uuid",
                "statusCode": 501,
                "timestamp": 1577836800.0,
            },
        },
        "headers": {"Content-Type": "application/json"},
    }


def test_missing_headers(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = {"httpMethod": "POST", "resource": "/test_request_resource/{path_level1}/{path_level2}"}

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)

    assert response == {
        "statusCode": 400,
        "body": "'headers' is a required property",
        "headers": {"Content-Type": "text/plain"},
    }


def test_wrong_body(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    from json import dumps

    event["body"] = loads(event["body"])
    event["body"]["body_key1"] = 123
    event["body"] = dumps(event["body"])

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)

    assert response == {
        "statusCode": 400,
        "body": "123 is not of type 'string'\n\n"
        "Failed validating 'type' in "
        "schema['properties']['body']['properties']['body_key1']:\n"
        "    {'description': 'containing only a string', 'type': 'string'}\n\n"
        "On instance['body']['body_key1']:\n"
        "    123",
        "headers": {"Content-Type": "text/plain"},
    }


def test_exception_with_raised_return_data(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(RaiseExpectedException).wrap_lambda(event, context)

    assert response == {
        "statusCode": 404,
        "body": "item in db not found",
        "headers": {"Content-Type": "text/plain"}
    }


def test_nested_api_resource(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_request_resource/specific_resource/{some_id}",
        pathParameters={"some_id": "test_id"},
    )

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)

    assert response == {"statusCode": 200}


@freeze_time("2020-01-01")
def test_expected_exception_and_return_api_response(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper._environ_variables import NoExceptDict

    environ["ERROR_LOG"] = NoExceptDict({"API_RESPONSE": True})

    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(RaiseExpectedException, with_context=True).wrap_lambda(event, context)
    response["body"] = loads(response["body"])

    assert response == {
        "statusCode": 404,
        "body": {
            "error": "item in db not found",
            "error_log": {
                "lambda_name": "test_function",
                "service_name": "group",
                "function_version": "$LATEST",
                "headers": {"Content-Type": "text/plain"},
                "aws_log_group": "test/log/group",
                "aws_request_id": "uuid",
                "statusCode": 404,
                "timestamp": 1577836800.0,
            },
        },
        "headers": {"Content-Type": "application/json"},
    }


def test_unexpected_exception(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(RaiseUnexpectedException).wrap_lambda(
        event, context
    )

    assert response == {
        "statusCode": 500,
        "body": "internal server error",
        "headers": {"Content-Type": "text/plain"},
    }


# @mark.skip
@mark.parametrize(
    "all_lower",
    (True, False)
)
@mark.parametrize(
    ("raised_exception_text", "statusCode", "expected_body"),
    (
        ("Unauthorized", 401, "Unauthorized"),
        ("Payment", 402, "Payment Required"),
        ("Forbidden", 403, "Forbidden"),
        (401, 401, "Unauthorized"),
        (402, 402, "Payment Required"),
        (403, 403, "Forbidden"),
    )
)
def test_unauthorized_exception(run_from_file_directory, raised_exception_text, statusCode, all_lower, expected_body):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfFunction

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    def exception_function(_):
        raise Exception(raised_exception_text.lower() if (all_lower and isinstance(raised_exception_text, str)) else raised_exception_text)

    response = LambdaHandlerOfFunction(exception_function).wrap_lambda(event.copy(), context)

    assert response == {
        "statusCode": statusCode,
        "body": expected_body,
        "headers": {"Content-Type": "text/plain"},
    }


test_body = {"body_key1": "some_string", "body_key2": {"sub_key1": "abc", "sub_key2": 34}}


@mark.parametrize(
    ("log_config", "expected_part_in_logging", "stated_log_level"),
    (
            ({"LOG_RAW_EVENT": True, "API_RESPONSE_VERIFICATION": False}, f": '{dumps(test_body)}'", "INFO"),
            ({"LOG_PARSED_EVENT": True, "API_RESPONSE_VERIFICATION": False}, f": {dumps(test_body)}", "INFO"),
            ({"LOG_PRE_PARSED_RESPONSE": True, "API_RESPONSE_VERIFICATION": False}, f": {dumps(test_body)}", "INFO"),
            ({"LOG_RAW_RESPONSE": True, "API_RESPONSE_VERIFICATION": False}, '"body": "{\\"', "INFO"),
    )
)
def test_logging_of_event_and_response(run_from_file_directory, caplog, log_config, expected_part_in_logging,
                                       stated_log_level):
    environ._load_config_from_file("api_response_wrapper_config.json")
    caplog.set_level(logging.INFO)
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    def returning_api(_):
        return {
            "statusCode": 200,
            "body": test_body,
            "headers": {"Content-Type": "application/json"}
        }

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_request_resource/{path_level1}/{path_level2}",
        pathParameters={"path_level1": "path_value1", "path_level2": "path_value2"},
        body=test_body
    )

    response = LambdaHandlerOfFunction(returning_api, **log_config).wrap_lambda(event.copy(), context)

    assert len(caplog.messages) == 1
    assert expected_part_in_logging in caplog.text
    assert caplog.text.startswith(stated_log_level)
    assert response["statusCode"] == 200


@mark.parametrize(
    "log_config",
    (
            {"LOG_PARSED_EVENT": True, "PARSE_BODY": False},
            {"LOG_PARSED_EVENT": True, "PARSE_EVENT_BODY": False},
            {"LOG_PRE_PARSED_RESPONSE": True, "PARSE_BODY": False},
            {"LOG_PRE_PARSED_RESPONSE": True, "PARSE_RESPONSE_BODY": False},
    )
)
def test_invalid_logging_config(run_from_file_directory, caplog, log_config):
    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_request_resource/{path_level1}/{path_level2}",
        pathParameters={"path_level1": "path_value1", "path_level2": "path_value2"},
        body=test_body
    )

    from jsonschema.exceptions import ValidationError
    with raises(ValidationError):
        LambdaHandlerOfFunction(api_basic, **log_config).wrap_lambda(event.copy(), context)
