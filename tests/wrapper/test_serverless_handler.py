from .._helper import context
from os.path import dirname, realpath
from os import chdir, getcwd
from aws_serverless_wrapper._helper.environ_variables import (
    environ,
    change_dict_to_no_except_dict,
)
from aws_serverless_wrapper.wrapper.base_class import ServerlessBaseClass
from pytest import fixture
from datesy.file_IO.json_file import load_single


@fixture
def run_from_file_directory():
    actual_cwd = getcwd()
    chdir(dirname(realpath(__file__)))
    yield
    chdir(actual_cwd)


def test_basic_function_run_through(run_from_file_directory):
    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    def api_basic(event_data):
        assert event_data == event

    LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)


def test_function_occurring_exception(run_from_file_directory):
    def api_basic():
        raise Exception("test")

    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.wrapper.serverless_handler import (
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
    def api_basic():
        raise Exception("test")

    environ._load_config_from_file("api_response_wrapper_config.json")

    environ["ERROR_LOG"] = change_dict_to_no_except_dict({"API_RESPONSE": True})

    from aws_serverless_wrapper.wrapper.serverless_handler import (
        LambdaHandlerOfFunction,
    )

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfFunction(api_basic).wrap_lambda(event, context)

    assert response["statusCode"] == 500
    assert response["headers"] == {"Content-Type": "application/json"}
    assert len(response["body"]) == 2
    assert len(response["body"]["error_log_item"]) == 10

    assert response["body"]["basic"] == "internal server error"
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


def test_basic_class_run_through(run_from_file_directory):
    class api_basic(ServerlessBaseClass):
        def main(self) -> dict:
            pass

    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

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
    ] = "../schema_validation/test_data/api/api_basic.json"
    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

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
    ] = "../schema_validation/test_data/api/api_basic-POST.json"
    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

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
    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    response = LambdaHandlerOfClass(EventHandler).wrap_lambda(event, context)
    assert response["statusCode"] == 200


def test_class_occurring_exception(run_from_file_directory):
    class api_basic(ServerlessBaseClass):
        def main(self) -> dict:
            raise Exception("test")

    environ._load_config_from_file("api_response_wrapper_config.json")
    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

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

    environ["ERROR_LOG"] = change_dict_to_no_except_dict({"API_RESPONSE": True})

    from aws_serverless_wrapper.wrapper.serverless_handler import LambdaHandlerOfClass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    response = LambdaHandlerOfClass(api_basic).wrap_lambda(event, context)

    assert response["statusCode"] == 500
    assert response["headers"] == {"Content-Type": "application/json"}
    assert len(response["body"]) == 2
    assert len(response["body"]["error_log_item"]) == 10

    assert response["body"]["basic"] == "internal server error"
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