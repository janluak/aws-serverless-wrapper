from freezegun import freeze_time
from testfixtures import LogCapture
from os import path
from .context_for_tests import context

exception_line_no = 10


def raise_exception(exception_text):
    raise Exception(exception_text)


def raise_exception_within(exception_text):
    raise_exception(exception_text)


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
    from aws_serverless_wrapper._helper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
    }

    assert _create_error_log_item(context=context,) == reference_exception_log_item


@freeze_time("2020-01-01")
def test_error_log_item_exception():
    from aws_serverless_wrapper._helper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        '"test_error_logging.py", '
        f"line {exception_line_no + 59}, in test_error_log_item_exception    "
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
    from aws_serverless_wrapper._helper.error_logging import _create_error_log_item

    exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
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
    from aws_serverless_wrapper._helper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        '"test_error_logging.py", '
        f"line {exception_line_no + 122}, in test_error_log_item_exception_additional_message    "
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
    from aws_serverless_wrapper._helper.error_logging import _create_error_log_item

    reference_exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": f'  File "test_error_logging.py", line {exception_line_no + 167}, in '
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
    from aws_serverless_wrapper._helper.error_logging import _create_error_log_item

    test_example_event_data = {
        "httpMethod": "POST",
        "headers": {"Accept": "application/json"},
        "body": {"key": "value"},
        "pathParameters": {"path_level1": "path_value1"},
        "queryParameters": {"key1": "value1"},
    }

    reference_exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
        "event_data": test_example_event_data,
    }

    assert (
        _create_error_log_item(context=context, event_data=test_example_event_data)
        == reference_exception_log_item
    )


@freeze_time("2020-01-01")
def test_error_log_item_with_exception_and_event_data():
    from aws_serverless_wrapper._helper.error_logging import _create_error_log_item

    test_example_event_data = {
        "httpMethod": "POST",
        "headers": {"Accept": "application/json"},
        "body": {"key": "value"},
        "pathParameters": {"path_level1": "path_value1"},
        "queryParameters": {"key1": "value1"},
    }

    reference_exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": "test_error_logging.py",
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        '"test_error_logging.py", '
        f"line {exception_line_no + 244}, in test_error_log_item_with_exception_and_event_data    "
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
    from aws_serverless_wrapper._helper import log_exception

    reference_exception_log_item = {
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
        "timestamp": "2020-01-01 00:00:00",
        "exception_type": "Exception",
        "exception_text": "exception text",
        "exception_file": path.realpath(__file__),
        "exception_line_no": exception_line_no,
        "exception_function": "raise_exception",
        "exception_stack": "  File "
        f'"{path.realpath(__file__)}", '
        f"line {exception_line_no + 289}, in {test_log_exception_to_logging_no_event_data.__name__}    "
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
                "aws_serverless_wrapper._helper.error_logging",
                "ERROR",
                str(reference_exception_log_item),
            )
        )

        assert log_item == reference_exception_log_item


from pytest import mark


@mark.skip("not implemented")
def test_log_exception_to_noSQL():
    pass


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
