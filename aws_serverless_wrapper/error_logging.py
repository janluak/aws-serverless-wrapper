from ._environ_variables import environ
import logging

logger = logging.getLogger(__name__)


__all__ = ["log_exception", "log_api_validation_error"]


def _create_error_log_item(
    context,
    exception: Exception = None,
    message: str = str(),
    event_data: dict = dict(),
):
    from datetime import datetime

    item = {
        "aws_request_id": context.aws_request_id,
        "aws_log_group": context.log_group_name,
        "service_name": context.log_group_name.split("/")[-1],
        "lambda_name": context.function_name,
        "function_version": context.function_version,
        "timestamp": datetime.utcnow().timestamp(),
    }

    if exception:
        if "statusCode" in exception.args[0]:
            item.update(exception.args[0])
        else:
            from traceback import format_exc

            tb = format_exc().splitlines()
            calls = tb[1:-1]

            raised_exception = tb[-1].split(":")
            raised_exception_type = raised_exception[0]
            raised_exception_text = raised_exception[1][1:]

            raised_exception_call = calls[-2]
            raised_exception_file = raised_exception_call.split('"')[1:2][0]
            raised_exception_line_no = int(
                raised_exception_call.split(",")[1].split(" ")[-1]
            )
            raised_exception_function = raised_exception_call.split(" ")[-1]

            item.update(
                {
                    "exception_type": raised_exception_type,
                    "exception_text": raised_exception_text,
                    "exception_file": raised_exception_file,
                    "exception_line_no": raised_exception_line_no,
                    "exception_function": raised_exception_function,
                    "exception_stack": "".join(calls),
                }
            )

    if message:
        item.update({"message": message})

    if event_data:
        item.update({"event_data": event_data})

    return item


def _log_error(exception, config, event_data, context, message=None):
    error_log_item = _create_error_log_item(
        context=context,
        exception=exception,
        event_data=event_data if config["LOG_EVENT_DATA"] else None,
        message=message,
    )

    logger.exception(error_log_item)

    if config["QUEUE"]:
        pass
    if config["DATABASE"]:
        if log_table_name := config["DATABASE"]["noSQL"]:
            from dynamo_db_resource import database_resource

            database_resource[log_table_name].put(error_log_item)

        if log_table_name := config["DATABASE"]["SQL"]:
            raise NotImplementedError

    if config["API_RESPONSE"]:
        return error_log_item


def log_api_validation_error(validation_exception, event_data, context):
    relevant_environ = environ["API_INPUT_VERIFICATION"]["LOG_ERRORS"]

    return _log_error(validation_exception, relevant_environ, event_data, context)


def log_exception(exception, event_data, context, message=None):
    relevant_environ = environ["ERROR_LOG"]

    return _log_error(exception, relevant_environ, event_data, context, message)
