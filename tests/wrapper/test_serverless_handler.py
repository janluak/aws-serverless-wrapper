from os.path import dirname, realpath
from os import chdir, getcwd
from aws_serverless_wrapper.testing import fake_context as context
from aws_serverless_wrapper._environ_variables import environ
from aws_serverless_wrapper.base_class import ServerlessBaseClass
from pytest import fixture
from fil_io.json import load_single
from json import loads


@fixture
def run_from_file_directory():
    actual_cwd = getcwd()
    chdir(dirname(realpath(__file__)))
    yield
    chdir(actual_cwd)


def test_basic_function_run_through(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    def api_basic(event_data):
        assert event_data == event

    LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)


def test_basic_function_run_through_no_verification(run_from_file_directory, caplog):
    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    def api_basic(event_data):
        assert event_data == event
        return {"statusCode": 200, "body": "Faulty Data", "headers": {"Content-Type": "text/plain"}}

    event["body"] = "wrong_body"
    assert LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)["statusCode"] != 200
    assert len(caplog.messages) == 1
    assert LambdaHandlerOfFunction(api_basic, PARSE_BODY=False, API_INPUT_VERIFICATION=False).wrap_lambda(event, context)["statusCode"] == 200
    assert len(caplog.messages) == 2
    assert "no specified response schema available" in caplog.text
    caplog.clear()
    environ._load_config_from_file("api_response_wrapper_config.json")

    assert LambdaHandlerOfFunction(api_basic, PARSE_BODY=False, API_INPUT_VERIFICATION=False, API_RESPONSE_VERIFICATION=False).wrap_lambda(event, context)["statusCode"] == 200
    assert len(caplog.messages) == 0


def test_function_occurring_exception(run_from_file_directory):
    def api_basic():
        raise Exception("test")

    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)

    assert response == {
        "statusCode": 500,
        "body": "internal server error",
        "headers": {"Content-Type": "text/plain"},
    }


def test_function_occurring_exception_with_error_log(run_from_file_directory):
    def api_basic(_):
        raise Exception("test")

    environ._load_config_from_file("api_response_wrapper_config.json")

    environ["ERROR_LOG"] = {"API_RESPONSE": True}

    from aws_serverless_wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)
    response["body"] = loads(response["body"])

    assert response["statusCode"] == 500
    assert response["headers"] == {"Content-Type": "application/json"}
    assert len(response["body"]) == 2
    assert len(response["body"]["error_log"]) == 12

    assert response["body"]["error"] == "internal server error"
    assert set(response["body"]["error_log"].keys()) == {
        "aws_request_id",
        "aws_log_group",
        "lambda_name",
        "service_name",
        "function_version",
        "timestamp",
        "exception_type",
        "exception_text",
        "exception_file",
        "exception_line_no",
        "exception_function",
        "exception_stack",
    }


def test_basic_class_run_through(run_from_file_directory):
    class api_basic(ServerlessBaseClass):
        def main(self) -> dict:
            pass

    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    response = LambdaHandlerOfClass(api_basic).wrap_lambda(event, context)
    assert response["statusCode"] == 200


def test_different_named_class_run_through(run_from_file_directory):
    class EventHandler(ServerlessBaseClass):
        def main(self) -> dict:
            pass

    environ._load_config_from_file("api_response_wrapper_config.json")
    environ["API_INPUT_VERIFICATION"][
        "SCHEMA_DIRECTORY"
    ] = "../schema_validation/test_data/api/test_request_resource||{path_level1}||{path_level2}.json"
    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    response = LambdaHandlerOfClass(EventHandler).wrap_lambda(event, context)
    assert response["statusCode"] == 200


def test_different_named_class_run_through_schema_with_http_method(
    run_from_file_directory,
):
    class EventHandler(ServerlessBaseClass):
        def main(self) -> dict:
            pass

    environ._load_config_from_file("api_response_wrapper_config.json")
    environ["API_INPUT_VERIFICATION"][
        "SCHEMA_DIRECTORY"
    ] = "../schema_validation/test_data/api/test_request_resource||{path_level1}||{path_level2}-POST.json"
    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    response = LambdaHandlerOfClass(EventHandler).wrap_lambda(event, context)
    assert response["statusCode"] == 200


def test_different_named_class_with_api_name_run_through(run_from_file_directory):
    class EventHandler(ServerlessBaseClass):

        api_name = "api_basic"

        def main(self) -> dict:
            pass

    environ._load_config_from_file("api_response_wrapper_config.json")
    environ["API_INPUT_VERIFICATION"][
        "SCHEMA_DIRECTORY"
    ] = "../schema_validation/test_data/api/"
    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    response = LambdaHandlerOfClass(EventHandler).wrap_lambda(event, context)
    assert response["statusCode"] == 200


def test_class_occurring_exception(run_from_file_directory):
    class api_basic(ServerlessBaseClass):
        def main(self) -> dict:
            raise Exception("test")

    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(api_basic).wrap_lambda(event, context)

    assert response == {
        "statusCode": 500,
        "body": "internal server error",
        "headers": {"Content-Type": "text/plain"},
    }


def test_class_occurring_exception_with_error_log(run_from_file_directory):
    class api_basic(ServerlessBaseClass):
        def main(self) -> dict:
            raise Exception("test")

    environ._load_config_from_file("api_response_wrapper_config.json")

    environ["ERROR_LOG"] = {"API_RESPONSE": True}

    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(api_basic).wrap_lambda(event, context)
    response["body"] = loads(response["body"])

    assert response["statusCode"] == 500
    assert response["headers"] == {"Content-Type": "application/json"}
    assert len(response["body"]) == 2
    assert len(response["body"]["error_log"]) == 12

    assert response["body"]["error"] == "internal server error"
    assert set(response["body"]["error_log"].keys()) == {
        "aws_request_id",
        "aws_log_group",
        "lambda_name",
        "service_name",
        "function_version",
        "timestamp",
        "exception_type",
        "exception_text",
        "exception_file",
        "exception_line_no",
        "exception_function",
        "exception_stack",
    }
