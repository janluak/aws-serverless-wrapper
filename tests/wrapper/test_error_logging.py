from freezegun import freeze_time
from testfixtures import LogCapture
from os import path
from json import dumps
from aws_serverless_wrapper.testing.context import fake_context as context

exception_line_no = 17


def raise_exception_with_http_status(code, body, content_type):
    raise Exception(
        {"statusCode": code, "body": body, "headers": {"Content-Type": content_type}}
    )


def raise_exception(exception_text):
    raise Exception(exception_text)


def raise_exception_within(exception_text):
    raise_exception(exception_text)


def raise_empty_exception():
    raise SystemError


def delete_origin_paths_from_traceback(string):
    while string.find('"/') > 0:
        start_pos = string.find('"/') + 1
        next_start_pos = string[start_pos + 1 :].find('"') + start_pos + 1
        while True:
            next_start_pos -= 1
            if string[next_start_pos] == "/":
                end_pos = next_start_pos
                break

        string = string[0:start_pos] + string[end_pos + 1 :]
    return string


@freeze_time("2020-01-01")
def test_error_log_item_basic():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "lambda_name": "test_function",
        "service_name": "group",
        "function_version": "$LATEST",
    }

    assert _create_error_log_item(context=context,) == reference_exception_log_item


@freeze_time("2020-01-01")
def test_error_log_item_exception():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "lambda_name": "test_function",
        "service_name": "group",
        "function_version": "$LATEST",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        '"test_error_logging.py", '
        f"line {exception_line_no + 63}, in test_error_log_item_exception    "
        'raise_exception("exception text")  File '
        '"test_error_logging.py", '
        f"line {exception_line_no}, in raise_exception    raise "
        "Exception(exception_text)",
    }

    try:
        raise_exception("exception text")
    except Exception as e:
        actual_item = _create_error_log_item(context=context, exception=e)

        assert (
            actual_item["exception_file"].split("/")[-1]
            == reference_exception_log_item["exception_file"]
        )
        del actual_item["exception_file"]
        del reference_exception_log_item["exception_file"]

        actual_item["exception_stack"] = delete_origin_paths_from_traceback(
            actual_item["exception_stack"]
        )

        assert actual_item == reference_exception_log_item


@freeze_time("2020-01-01")
def test_error_log_item_message():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "lambda_name": "test_function",
        "service_name": "group",
        "function_version": "$LATEST",
        "message": "some message for logging an error",
    }

    assert (
        _create_error_log_item(
            context=context, message="some message for logging an error"
        )
        == exception_log_item
    )


@freeze_time("2020-01-01")
def test_error_log_item_exception_additional_message():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "lambda_name": "test_function",
        "service_name": "group",
        "function_version": "$LATEST",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        '"test_error_logging.py", '
        f"line {exception_line_no + 130}, in test_error_log_item_exception_additional_message    "
        'raise_exception("exception text")  File '
        '"test_error_logging.py", '
        f"line {exception_line_no}, in raise_exception    raise "
        "Exception(exception_text)",
        "message": "some message for logging an error",
    }

    try:
        raise_exception("exception text")
    except Exception as e:
        actual_item = _create_error_log_item(
            context=context, exception=e, message="some message for logging an error"
        )

        assert (
            actual_item["exception_file"].split("/")[-1]
            == reference_exception_log_item["exception_file"]
        )
        del actual_item["exception_file"]
        del reference_exception_log_item["exception_file"]

        actual_item["exception_stack"] = delete_origin_paths_from_traceback(
            actual_item["exception_stack"]
        )

        assert actual_item == reference_exception_log_item


@freeze_time("2020-01-01")
def test_error_log_item_hierarchy_exception():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "service_name": "group",
        "function_version": "$LATEST",
        "lambda_name": "test_function",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": f'  File "test_error_logging.py", line {exception_line_no + 177}, in '
        "test_error_log_item_hierarchy_exception    "
        'raise_exception_within("exception text")  File '
        f'"test_error_logging.py", line {exception_line_no + 4}, in '
        "raise_exception_within    "
        "raise_exception(exception_text)  File "
        f'"test_error_logging.py", line {exception_line_no}, in raise_exception    '
        "raise Exception(exception_text)",
    }

    try:
        raise_exception_within("exception text")
    except Exception as e:
        actual_item = _create_error_log_item(context=context, exception=e)

        assert (
            actual_item["exception_file"].split("/")[-1]
            == reference_exception_log_item["exception_file"]
        )
        del actual_item["exception_file"]
        del reference_exception_log_item["exception_file"]

        actual_item["exception_stack"] = delete_origin_paths_from_traceback(
            actual_item["exception_stack"]
        )

        assert actual_item == reference_exception_log_item


@freeze_time("2020-01-01")
def test_error_log_item_with_event_data():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    test_example_event_data = {
        "httpMethod": "POST",
        "headers": {"Accept": "application/json"},
        "body": {"key": "value"},
        "pathParameters": {"path_level1": "path_value1"},
        "queryParameters": {"key1": "value1"},
    }

    reference_exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "service_name": "group",
        "function_version": "$LATEST",
        "lambda_name": "test_function",
        "event_data": test_example_event_data,
    }

    assert (
        _create_error_log_item(context=context, event_data=test_example_event_data)
        == reference_exception_log_item
    )


@freeze_time("2020-01-01")
def test_error_log_item_with_exception_and_event_data():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    test_example_event_data = {
        "httpMethod": "POST",
        "headers": {"Accept": "application/json"},
        "body": {"key": "value"},
        "pathParameters": {"path_level1": "path_value1"},
        "queryParameters": {"key1": "value1"},
    }

    reference_exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "service_name": "group",
        "function_version": "$LATEST",
        "lambda_name": "test_function",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        '"test_error_logging.py", '
        f"line {exception_line_no + 258}, in test_error_log_item_with_exception_and_event_data    "
        'raise_exception("exception text")  File '
        '"test_error_logging.py", '
        f"line {exception_line_no}, in raise_exception    raise "
        "Exception(exception_text)",
        "event_data": test_example_event_data,
    }

    try:
        raise_exception("exception text")
    except Exception as e:
        actual_item = _create_error_log_item(
            context=context, event_data=test_example_event_data, exception=e
        )

        assert (
            actual_item["exception_file"].split("/")[-1]
            == reference_exception_log_item["exception_file"]
        )
        del actual_item["exception_file"]
        del reference_exception_log_item["exception_file"]

        actual_item["exception_stack"] = delete_origin_paths_from_traceback(
            actual_item["exception_stack"]
        )

        assert actual_item == reference_exception_log_item


@freeze_time("2020-01-01")
def test_log_exception_to_logging_no_event_data():
    from aws_serverless_wrapper._environ_variables import environ

    environ["ERROR_LOG"] = {"API_RESPONSE": True}
    from aws_serverless_wrapper.error_logging import log_exception

    reference_exception_log_item = {
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "service_name": "group",
        "lambda_name": "test_function",
        "function_version": "$LATEST",
        "timestamp": 1577836800.0,
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": path.realpath(__file__),
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        f'"{path.realpath(__file__)}", '
        f"line {exception_line_no + 308}, in {test_log_exception_to_logging_no_event_data.__name__}    "
        'raise_exception("exception text")  File '
        f'"{path.realpath(__file__)}", '
        f"line {exception_line_no}, in raise_exception    raise "
        "Exception(exception_text)",
    }

    with LogCapture() as log_capture:
        try:
            raise_exception("exception text")
        except Exception as e:
            log_item = log_exception(exception=e, event_data=dict(), context=context)

        log_capture.check(
            (
                "aws_serverless_wrapper.error_logging",
                "ERROR",
                dumps(reference_exception_log_item),
            )
        )

        assert log_item == reference_exception_log_item


@freeze_time("2020-01-01")
def test_log_exception_based_on_thrown_status_code_exception():
    from aws_serverless_wrapper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": 1577836800.0,
        "aws_request_id": "uuid",
        "aws_log_group": "test/log/group",
        "lambda_name": "test_function",
        "service_name": "group",
        "function_version": "$LATEST",
        "statusCode": 404,
        "body": "not found",
        "headers": {"Content-Type": "text/plain"},
    }

    try:
        raise_exception_with_http_status(404, "not found", "text/plain")
    except Exception as e:
        actual_item = _create_error_log_item(context=context, exception=e)

        assert actual_item == reference_exception_log_item


@freeze_time("2020-01-01")
def test_log_empty_exception():
    from aws_serverless_wrapper.error_logging import handle_exception
    from aws_serverless_wrapper.testing import fake_context

    class Handler:
        request_data = dict()
        context = fake_context

    try:
        raise_empty_exception()
    except Exception as e:
        handle_exception(Handler, e)


from pytest import mark


@mark.skip("not implemented")
def test_log_exception_to_SQL():
    pass


@mark.skip("not implemented")
def test_log_exception_to_queue():
    pass


@mark.skip("not implemented")
def test_log_api_validation_to_logging():
    pass


@mark.skip("not implemented")
def test_log_api_validation_to_noSQL():
    pass


@mark.skip("not implemented")
def test_log_api_validation_to_SQL():
    pass


@mark.skip("not implemented")
def test_log_api_validation_to_queue():
    pass
