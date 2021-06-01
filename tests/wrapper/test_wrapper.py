from aws_serverless_wrapper._environ_variables import environ
from aws_serverless_wrapper.testing import fake_context as context
from fil_io.json import load_single
from pytest import fixture, raises, mark
from os.path import dirname, realpath
from os import chdir, getcwd


@fixture
def run_from_file_directory():
    actual_cwd = getcwd()
    chdir(dirname(realpath(__file__)))
    yield
    chdir(actual_cwd)


def test_function_run_through(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper

    environ._load_config_from_file("api_response_wrapper_config.json")

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    @aws_serverless_wrapper
    def api_basic(event_data):
        assert event_data == event

    response = api_basic(event, context)
    assert response["statusCode"] == 200


def test_function_run_through_response_from_function(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper

    environ._load_config_from_file("api_response_wrapper_config.json")

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    @aws_serverless_wrapper
    def api_basic(event_data):
        return {
            "statusCode": 400,
            "body": "some response text",
            "headers": {"Content-Type": "text/plain"},
        }

    response = api_basic(event, context)
    assert response["statusCode"] == 400
    assert response["body"] == "some response text"
    assert response["headers"] == {"Content-Type": "text/plain"}


def test_class_run_through(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper, ServerlessBaseClass

    environ._load_config_from_file("api_response_wrapper_config.json")

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    @aws_serverless_wrapper
    class api_basic(ServerlessBaseClass):
        def main(self):
            assert self.event == event
            assert self.context == context

    response = api_basic(event, context)
    assert response["statusCode"] == 200


def test_class_run_through_with_response(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper, ServerlessBaseClass

    @aws_serverless_wrapper
    class api_basic(ServerlessBaseClass):
        def main(self):
            return {
                "statusCode": 400,
                "body": "some response text",
                "headers": {"Content-Type": "text/plain"},
            }

    environ._load_config_from_file("api_response_wrapper_config.json")

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")
    response = api_basic(event, context)
    assert response["statusCode"] == 400
    assert response["body"] == "some response text"
    assert response["headers"] == {"Content-Type": "text/plain"}


def test_class_wrong_base_class(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper, ServerlessBaseClass

    with raises(TypeError) as te:

        @aws_serverless_wrapper
        class api_basic:
            def main(self):
                pass

        api_basic()

        assert (
            te.value.args[0]
            == f"if given a class it must derive from aws_serverless_wrapper.{ServerlessBaseClass.__name__}"
        )


def test_class_base_class_missing_handler(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper, ServerlessBaseClass

    environ["ERROR_LOG"] = {"API_RESPONSE": True}

    @aws_serverless_wrapper
    class api_basic(ServerlessBaseClass):
        pass

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    with raises(TypeError) as te:
        response = api_basic(event, context)
        assert (
            te.value.args[0]
            == f"Can't instantiate abstract class api_basic with abstract methods main"
        )


def test_function_with_context(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper

    environ._load_config_from_file("api_response_wrapper_config.json")

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    @aws_serverless_wrapper(with_context=True)
    def api_basic(event_data, context_data):
        assert event_data == event
        assert context_data == context

    response = api_basic(event, context)
    assert response["statusCode"] == 200


def test_wrapper_with_charset_utf8_content_type(run_from_file_directory):
    from aws_serverless_wrapper import aws_serverless_wrapper

    environ._load_config_from_file("api_response_wrapper_config.json")

    event = load_single(f"../schema_validation/test_data/api/request_basic.json")

    event["headers"]["Content-Type"] += "; charset=utf-8"

    @aws_serverless_wrapper
    def api_basic(event_data):
        assert event_data == event

    response = api_basic(event, context)
    assert response["statusCode"] == 200
