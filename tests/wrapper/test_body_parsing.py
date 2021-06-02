from pytest import raises
from copy import deepcopy


def test_text_plain():
    from aws_serverless_wrapper._body_parsing import text_plain
    test_data = "some test string"
    assert text_plain(test_data) == test_data


def test_text_plain_false_input():
    from aws_serverless_wrapper._body_parsing import text_plain
    test_data = 1234
    with raises(TypeError) as e:
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

    with raises(TypeError) as e:
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

    with raises(TypeError) as TE:
        application_x_www_form_urlencoded(test_string)

    assert TE.value.args[0] == {
        "statusCode": 400,
        "body": "Body has to be x-www-form-urlencoded formatted",
        "headers": {"Content-Type": "text/plain"}
    }
