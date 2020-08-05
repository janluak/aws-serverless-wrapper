from aws_serverless_wrapper.testing import predefined_context as context
from os.path import dirname, realpath
from os import chdir, getcwd
from freezegun import freeze_time
from pytest import fixture
from datesy.file_IO.json_file import load_single
from aws_serverless_wrapper._helper import environ
from aws_serverless_wrapper import ServerlessBaseClass


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

    from aws_serverless_wrapper.wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = {"httpMethod": "WRONG"}

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

    from aws_serverless_wrapper.wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = {"httpMethod": "WRONG"}

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)
    assert response == {
        "statusCode": 501,
        "body": {
            "basic": "API is not defined",
            "error_log_item": {
                "body": "API is not defined",
                "lambda_name": "test_function",
                "service_name": "group",
                "function_version": "$LATEST",
                "headers": {"Content-Type": "text/plain"},
                "aws_log_group": "test/log/group",
                "aws_request_id": "uuid",
                "statusCode": 501,
                "timestamp": "2020-01-01 00:00:00",
            },
        },
        "headers": {"Content-Type": "application/json"},
    }


def test_missing_headers(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = {"httpMethod": "POST"}

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)

    assert response == {
        "statusCode": 400,
        "body": "headers has to be included",
        "headers": {"Content-Type": "text/plain"},
    }


def test_wrong_body(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    from json import loads, dumps

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


def test_exception_with_raised_status_code(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(RaiseExpectedException).wrap_lambda(event, context)

    assert response == {"statusCode": 200}


@freeze_time("2020-01-01")
def test_expected_exception_and_return_api_response(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper._helper.environ_variables import NoExceptDict

    environ["ERROR_LOG"] = NoExceptDict({"API_RESPONSE": True})

    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(RaiseExpectedException).wrap_lambda(event, context)

    assert response == {
        "statusCode": 200,
        "body": {
            "basic": "internally captured error",
            "error_log_item": {
                "body": "item in db not found",
                "lambda_name": "test_function",
                "service_name": "group",
                "function_version": "$LATEST",
                "headers": {"Content-Type": "text/plain"},
                "aws_log_group": "test/log/group",
                "aws_request_id": "uuid",
                "statusCode": 404,
                "timestamp": "2020-01-01 00:00:00",
            },
        },
        "headers": {"Content-Type": "application/json"},
    }


def test_unexpected_exception(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(RaiseUnexpectedException).wrap_lambda(
        event, context
    )

    assert response == {
        "statusCode": 500,
        "body": "internal server error",
        "headers": {"Content-Type": "text/plain"},
    }
