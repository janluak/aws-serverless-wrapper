from ._environ_variables import environ
import logging
from requests.status_codes import _codes, codes
from json import dumps

logger = logging.getLogger(__name__)


__all__ = ["handle_exception", "log_exception", "log_api_validation_error"]


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
        if exception.args:
            exception_data = exception.args[0]
        else:
            exception_data = str()
        if isinstance(exception_data, dict) and "statusCode" in exception_data:
            item.update(exception_data)
        else:
            from traceback import format_exc

            tb = format_exc().splitlines()
            calls = tb[1:-1]

            raised_exception = tb[-1].split(":")
            raised_exception_type = raised_exception[0]
            if len(raised_exception) > 1:
                raised_exception_text = raised_exception[1][1:]
            else:
                raised_exception_text = str()

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


def _log_error(exception, status_code, config, event_data, context, message=None):
    error_log_item = _create_error_log_item(
        context=context,
        exception=exception,
        event_data=event_data if config.get("LOG_EVENT_DATA", None) else None,
        message=message,
    )

    if status_code is None or status_code >= 500:
        logger.exception(dumps(error_log_item))
    elif status_code >= 400:
        logger.warning(dumps(error_log_item))

    if config.get("QUEUE", None):
        pass
    if config.get("DATABASE", None):
        if log_table_name := config["DATABASE"].get("noSQL", None):
            from dynamo_db_resource import database_resource

            database_resource[log_table_name].put(error_log_item)

        if log_table_name := config["DATABASE"].get("SQL", None):
            raise NotImplementedError

    if config.get("API_RESPONSE", None):
        error_log_item.pop("body", None)
        error_log_item.pop("message", None)
        return error_log_item


def log_api_validation_error(validation_exception, event_data, context):
    relevant_environ = environ["API_INPUT_VERIFICATION"]["LOG_ERRORS"]
    return _log_error(validation_exception, 501, relevant_environ, event_data, context)


def log_exception(exception, event_data, context, status_code=None, message=None):
    relevant_environ = environ["ERROR_LOG"]
    return _log_error(exception, status_code, relevant_environ, event_data, context, message)


def handle_exception(handler, exc):
    if exc.args:
        exception_data = exc.args[0]
    else:
        exception_data = str()
    status_code = 500
    body = "internal server error"
    headers = {"Content-Type": "text/plain"}
    if isinstance(exception_data, dict):
        status_code = exception_data.get("statusCode", status_code)
        body = exception_data.get("body", body)

    elif isinstance(exception_data, int):
        status_code = exception_data
        body = " ".join(i.capitalize() for i in _codes[exception_data][0].split("_"))

    elif "abstract class" in exception_data:
        raise exc

    else:
        if casted_code := codes["_".join(exception_data.split(" ")).lower()]:
            status_code = casted_code
            body = " ".join(i.capitalize() for i in _codes[status_code][0].split("_"))

    if environ["API_INPUT_VERIFICATION"]["LOG_ERRORS"]["API_RESPONSE"] and status_code == 501 and "API" in body:
        if error_log_item := log_api_validation_error(exc, handler.request_data, handler.context):
            headers = {"Content-Type": "application/json"}
            body = {
                "error": body,
                "error_log": error_log_item
            }

    else:
        error_log_item = log_exception(
            exc,
            handler.request_data,
            handler.context,
            status_code,
            body if not (isinstance(exception_data, dict) and "body" in exception_data) else None
        )
        if environ["ERROR_LOG"]["API_RESPONSE"]:
            headers = {"Content-Type": "application/json"}
            body = {
                "error": body,
                "error_log": error_log_item
            }

    return {
        "statusCode": status_code,
        "body": body,
        "headers": headers
    }
