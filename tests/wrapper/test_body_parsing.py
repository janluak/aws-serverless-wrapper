from pytest import raises
from copy import deepcopy


def test_text_plain():
    from aws_serverless_wrapper.wrapper._body_parsing import text_plain
    test_data = "some test string"
    assert text_plain(test_data) == test_data


def test_text_plain_false_input():
    from aws_serverless_wrapper.wrapper._body_parsing import text_plain
    test_data = 1234
    with raises(TypeError) as e:
        text_plain(test_data)

    assert e.value.args[0] == {
            "statusCode": 400,
            "body": "Body has to be plain text",
            "headers": {"Content-Type": "text/plain"},
        }


def test_select_text_plain():
    from aws_serverless_wrapper.wrapper._body_parsing import parse_body
    test_data = {
        "body": 'just some text',
        "headers": {"content-type": "text/plain"}
    }

    assert parse_body(test_data) == test_data


def test_dump_json():
    from json import dumps
    from aws_serverless_wrapper.wrapper._body_parsing import application_json
    test_data = {"key1": "value1"}

    assert application_json(test_data) == dumps(test_data)


def test_dump_json_list():
    from json import dumps
    from aws_serverless_wrapper.wrapper._body_parsing import application_json
    test_data = [{"key1": "value1"}]

    assert application_json(test_data) == dumps(test_data)


def test_load_json():
    from json import dumps
    from aws_serverless_wrapper.wrapper._body_parsing import application_json
    test_data = {"key1": "value1"}

    assert application_json(dumps(test_data)) == test_data


def test_load_json_exception():
    from aws_serverless_wrapper.wrapper._body_parsing import application_json
    test_data = '{"key1": "value1"'

    with raises(TypeError) as e:
        application_json(test_data)

    assert e.value.args[0] == {
            "statusCode": 400,
            "body": "Body has to be json formatted",
            "headers": {"Content-Type": "text/plain"},
        }


def test_select_application_json_dumping():
    from json import dumps
    from aws_serverless_wrapper.wrapper._body_parsing import parse_body
    test_data = {
        "body": {"key1": "value1"},
        "headers": {"content-type": "application/json"}
    }

    expected_item = deepcopy(test_data)
    expected_item["body"] = dumps(expected_item["body"])

    assert parse_body(test_data) == expected_item


def test_select_empty_body():
    from json import dumps
    from aws_serverless_wrapper.wrapper._body_parsing import parse_body
    test_data = {
        "body": dict(),
        "headers": dict()
    }

    assert parse_body(test_data) == test_data

    test_data = {
        "body": None,
        "headers": dict()
    }

    assert parse_body(test_data) == test_data
