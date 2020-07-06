from freezegun import freeze_time


class Namespace:
    """Simple object for storing attributes.

    Implements equality by attribute names and values, and provides a simple
    string representation.

    Copied from argparse.ArgumentParser
    """

    def __init__(self, **kwargs):
        for name in kwargs:
            setattr(self, name, kwargs[name])

    def __eq__(self, other):
        if not isinstance(other, Namespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __contains__(self, key):
        return key in self.__dict__


context = Namespace(
    **{
        "aws_request_id": "uuid",
        "log_group_name": "test/log/group",
        "function_name": "test_function",
    }
)

exception_line_no = 38


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
    from aws_serverless_wrapper._helper import create_error_log_item

    reference_exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
    }

    assert create_error_log_item(context=context,) == reference_exception_log_item


@freeze_time("2020-01-01")
def test_error_log_item_exception():
    from aws_serverless_wrapper._helper import create_error_log_item

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
        actual_item = create_error_log_item(context=context, exception=e)

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
    from aws_serverless_wrapper._helper import create_error_log_item

    exception_log_item = {
        "timestamp": "2020-01-01 00:00:00",
        "request_id": "uuid",
        "log_group": "test/log/group",
        "function_name": "test_function",
        "message": "some message for logging an error",
    }

    assert (
        create_error_log_item(
            context=context, message="some message for logging an error"
        )
        == exception_log_item
    )


@freeze_time("2020-01-01")
def test_error_log_item_exception_additional_message():
    from aws_serverless_wrapper._helper import create_error_log_item

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
        actual_item = create_error_log_item(
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
    from aws_serverless_wrapper._helper import create_error_log_item

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
        actual_item = create_error_log_item(context=context, exception=e)

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
    from aws_serverless_wrapper._helper import create_error_log_item

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
        create_error_log_item(context=context, event_data=test_example_event_data)
        == reference_exception_log_item
    )


@freeze_time("2020-01-01")
def test_error_log_item_with_exception_and_event_data():
    from aws_serverless_wrapper._helper import create_error_log_item

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
        actual_item = create_error_log_item(
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
