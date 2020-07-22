from .._helper import context
from os.path import dirname, realpath
from os import chdir, getcwd
from freezegun import freeze_time
from pytest import fixture
from datesy.file_IO.json_file import load_single
from aws_serverless_wrapper._helper import environ


def api_basic(event):
    pass


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

    assert response["statusCode"] == 501
    assert response["headers"] == {"Content-Type": "application/json"}
    assert len(response["body"]) == 2
    assert len(response["body"]["error_log_item"]) == 10

    assert response["body"]["basic"] == "API is not defined"

    assert set(response["body"]["error_log_item"].keys()) == {
        "request_id",
        "log_group",
        "function_name",
        "timestamp",
        "exception_type",
        "exception_text",
        "exception_file",
        "exception_line_no",
        "exception_function",
        "exception_stack",
    }
    print(response["body"]["error_log_item"])


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
    event["body"]["body_key1"] = 123

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
