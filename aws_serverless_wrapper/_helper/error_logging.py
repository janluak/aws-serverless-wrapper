__all__ = ["create_error_log_item"]


def create_error_log_item(
    context,
    exception: Exception = None,
    message: str = str(),
    event_data: dict = dict(),
):
    from datetime import datetime

    item = {
        "request_id": context.aws_request_id,
        "log_group": context.log_group_name,
        "function_name": context.function_name,
        "timestamp": str(datetime.utcnow()),
    }

    if exception:
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