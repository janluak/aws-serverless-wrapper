from pytest import raises, mark
from copy import deepcopy
from .test_api_responses import run_from_file_directory
from aws_serverless_wrapper.testing import compose_ReST_event, fake_context
from aws_serverless_wrapper._body_parsing import ParsingError


def test_text_plain():
    from aws_serverless_wrapper._body_parsing import text_plain
    test_data = "some test string"
    assert text_plain(test_data) == test_data


def test_text_plain_false_input():
    from aws_serverless_wrapper._body_parsing import text_plain
    test_data = 1234
    with raises(ParsingError) as e:
        text_plain(test_data)

    assert e.value.args[0] == {
        "statusCode": 400,
        "body": "Body has to be plain text",
        "headers": {"Content-Type": "text/plain"},
    }


def test_select_text_plain():
    from aws_serverless_wrapper._body_parsing import parse_body
    test_data = {
        "body": 'just some text',
        "headers": {"content-type": "text/plain"}
    }

    assert parse_body(test_data) == test_data


def test_dump_json():
    from json import dumps
    from aws_serverless_wrapper._body_parsing import application_json
    test_data = {"key1": "value1"}

    assert application_json(test_data) == dumps(test_data)


def test_dump_json_list():
    from json import dumps
    from aws_serverless_wrapper._body_parsing import application_json
    test_data = [{"key1": "value1"}]

    assert application_json(test_data) == dumps(test_data)


def test_load_json():
    from json import dumps
    from aws_serverless_wrapper._body_parsing import application_json
    test_data = {"key1": "value1"}

    assert application_json(dumps(test_data)) == test_data


def test_load_json_exception():
    from aws_serverless_wrapper._body_parsing import application_json
    test_data = '{"key1": "value1"'

    with raises(ParsingError) as e:
        application_json(test_data)

    assert e.value.args[0] == {
        "statusCode": 400,
        "body": "Body has to be json formatted",
        "headers": {"Content-Type": "text/plain"},
    }


def test_select_application_json_dumping():
    from json import dumps
    from aws_serverless_wrapper._body_parsing import parse_body
    test_data = {
        "body": {"key1": "value1"},
        "headers": {"content-type": "application/json"}
    }

    expected_item = deepcopy(test_data)
    expected_item["body"] = dumps(expected_item["body"])

    assert parse_body(test_data) == expected_item


def test_none_body_from_aws_request_data():
    from aws_serverless_wrapper._body_parsing import parse_body

    test_data = {
        "body": None,
        "headers": dict()
    }

    assert parse_body(test_data) == test_data


def test_unknown_content_type(caplog):
    from aws_serverless_wrapper._body_parsing import parse_body
    test_data = {
        "body": {"key1": "value1"},
        "headers": {"content-type": "x-custom/unsupported"}
    }

    with raises(NotImplementedError) as NE:
        parse_body(test_data)

    assert NE.value.args[0] == {
        "statusCode": 501,
        "body": "parsing of Content-Type 'x-custom/unsupported' not implemented",
        "headers": {"Content-Type": "text/plain"}
    }


def test_empty_list(caplog):
    from aws_serverless_wrapper._body_parsing import parse_body

    test_data = {
        "body": [],
        "headers": {"content-type": "application/json"}
    }

    response = parse_body(test_data)
    assert response == {
        "body": "[]",
        "headers": {"content-type": "application/json"}
    }


def test_application_x_www_form_urlencoded():
    from aws_serverless_wrapper._body_parsing import application_x_www_form_urlencoded

    test_string = "Key1=Value1&Key2=Value2"
    test_dict = {"Key1": "Value1", "Key2": "Value2"}

    assert application_x_www_form_urlencoded(test_string) == {k: [v] for k, v in test_dict.items()}
    assert application_x_www_form_urlencoded(test_dict) == test_string

    test_string = "Key1=Value1&Key2=Value2&DoubleKey=1&DoubleKey=2"
    test_dict = {"Key1": "Value1", "Key2": "Value2", "DoubleKey": ["1", "2"]}

    assert application_x_www_form_urlencoded(test_string) == {
        'DoubleKey': ['1', '2'], 'Key1': ['Value1'], 'Key2': ['Value2']
    }
    assert application_x_www_form_urlencoded(test_dict) == "Key1=Value1&Key2=Value2&DoubleKey=%5B%271%27%2C+%272%27%5D"


def test_application_x_www_form_urlencoded_with_charset():
    from aws_serverless_wrapper._body_parsing import application_x_www_form_urlencoded

    test_string = "Key1=Value1&Key2=Value2"
    test_dict = {"Key1": "Value1", "Key2": "Value2"}

    assert application_x_www_form_urlencoded(test_string, "utf-8") == {k: [v] for k, v in test_dict.items()}

    from aws_serverless_wrapper._body_parsing import parse_body

    test_requrest = {"headers": {"Content-Type": "application/x-www-form-urlencoded"}, "body": test_string}
    assert parse_body(test_requrest) == {
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "body": {k: [v] for k, v in test_dict.items()}
    }


def test_application_x_www_form_urlencoded_erors():
    from aws_serverless_wrapper._body_parsing import application_x_www_form_urlencoded

    test_string = "abc"

    with raises(ParsingError) as TE:
        application_x_www_form_urlencoded(test_string)

    assert TE.value.args[0] == {
        "statusCode": 400,
        "body": "Body has to be x-www-form-urlencoded formatted",
        "headers": {"Content-Type": "text/plain"}
    }


@mark.parametrize(
    ("parse_config", "response_components", "event_body", "return_body", "raised_exception"),
    (
            (dict(), {"statusCode": 200},
             "{\"body_key1\": \"value1\", \"body_key2\": "
             "{\"sub_body_key2.1\": \"value1\", \"sub_body_key2.2\": \"value2\"}}",
             {"key": "value"}, None),
            (dict(), {"statusCode": 400, "body": "Body has to be json formatted"}, "some string body", {"key": "value"}, None),
            ({"PARSE_EVENT_BODY": False}, {"statusCode": 200}, "some string body", {"key": "value"}, None),
            ({"PARSE_BODY": False}, {"statusCode": 200}, "some string body", {"key": "value"}, None),
            (dict(), {"statusCode": 400}, "{\"body_key1\": \"value1\", \"body_key2\": "
             "{\"sub_body_key2.1\": \"value1\", \"sub_body_key2.2\": \"value2\"}}", "some string body", ParsingError),
            ({"PARSE_RESPONSE_BODY": False}, {"statusCode": 200}, "{\"body_key1\": \"value1\", \"body_key2\": "
             "{\"sub_body_key2.1\": \"value1\", \"sub_body_key2.2\": \"value2\"}}", "some string body", None),
            ({"PARSE_BODY": False}, {"statusCode": 200}, "{\"body_key1\": \"value1\", \"body_key2\": "
             "{\"sub_body_key2.1\": \"value1\", \"sub_body_key2.2\": \"value2\"}}", "some string body", None)
    )
)
def test_parsing_config(caplog, run_from_file_directory, parse_config, response_components, event_body, return_body, raised_exception):
    def test_func(_):
        return {
            "statusCode": 200,
            "body": return_body,
            "headers": {"Content-Type": "application/json"}
        }

    from aws_serverless_wrapper._environ_variables import environ
    environ._load_config_from_file("api_response_wrapper_config.json")

    from aws_serverless_wrapper.serverless_handler import LambdaHandlerOfFunction

    event = compose_ReST_event(
        httpMethod="POST",
        resource="/test_request_no_verification",
        headers={"Content-Type": "application/json"}
    )
    event["body"] = event_body

    if not raised_exception:
        response = LambdaHandlerOfFunction(test_func, **parse_config).wrap_lambda(event, fake_context)
        for key in response_components:
            assert response[key] == response_components[key]
    else:
        with raises(raised_exception):
            LambdaHandlerOfFunction(test_func, **parse_config).wrap_lambda(event, fake_context)
