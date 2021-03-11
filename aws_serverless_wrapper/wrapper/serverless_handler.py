from abc import ABC, abstractmethod
from .base_class import ServerlessBaseClass
from aws_environ_helper import environ
from jsonschema.exceptions import ValidationError
from datetime import datetime
from types import FunctionType
from ._body_parsing import parse_body


__all__ = ["LambdaHandlerOfClass", "LambdaHandlerOfFunction"]

try:
    globals()["METRICS"]
except KeyError:
    METRICS = {
        "container_initiation_time": datetime.utcnow(),
        "container_reusing_count": 0,
    }


class __LambdaHandler(ABC):
    def __init__(
        self, business_handler: (ServerlessBaseClass.__subclasses__(), FunctionType)
    ):
        self.business_handler = business_handler
        self.request_data = None
        self.context = None

    @abstractmethod
    def run(self):
        pass

    @property
    @abstractmethod
    def api_name(self) -> str:
        return str()

    def input_verification(self) -> (None, dict):
        try:
            self.request_data = parse_body(self.request_data)

            if environ["API_INPUT_VERIFICATION"]:
                from aws_schema import APIDataValidator

                origin_type = environ["API_INPUT_VERIFICATION"]["SCHEMA_ORIGIN"]
                origin_value = environ["API_INPUT_VERIFICATION"]["SCHEMA_DIRECTORY"]

                self.request_data = APIDataValidator(
                    self.request_data, self.api_name, **{origin_type: origin_value},
                ).data
        except (OSError, TypeError, ValidationError) as e:
            from aws_environ_helper import log_api_validation_error

            error_log_item = log_api_validation_error(e, self.request_data, self.context)

            if not error_log_item:
                return e.args[0]

            else:
                return {
                    "statusCode": e.args[0]["statusCode"],
                    "body": {
                        "basic": e.args[0]["body"],
                        "error_log_item": error_log_item,
                    },
                    "headers": {"Content-Type": "application/json"},
                }

    def output_verification(self, response):
        if environ["API_RESPONSE_VERIFICATION"]:
            from aws_schema import ResponseDataValidator

            origin_type = environ["API_RESPONSE_VERIFICATION"]["SCHEMA_ORIGIN"]
            origin_value = environ["API_RESPONSE_VERIFICATION"]["SCHEMA_DIRECTORY"]

            ResponseDataValidator(
                response,
                httpMethod=self.request_data["httpMethod"],
                api_name=self.api_name,
                **{origin_type: origin_value},
            )

    def _log_error(self, exc):
        if "abstract class" in exc.args[0]:
            raise exc

        if environ["ERROR_LOG"]["API_RESPONSE"]:
            from aws_environ_helper import log_exception

            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "basic": "internal server error",
                    "error_log_item": log_exception(exc, self.request_data, self.context),
                }
            }

        else:
            return {
                "statusCode": 500,
                "body": "internal server error",
                "headers": {"Content-Type": "text/plain"},
            }

    def wrap_lambda(self, event, context) -> dict:
        METRICS["container_reusing_count"] += 1

        self.request_data = event
        self.context = context
        if bad_input_response := self.input_verification():
            return parse_body(bad_input_response)

        try:
            if response := self.run():
                self.output_verification(response)
            else:
                response = {"statusCode": 200}
        except NotImplementedError as e:
            from aws_environ_helper import log_exception
            log_exception(e, self.request_data, self.context)
            response = e.args[0]
        except Exception as e:
            response = self._log_error(e)

        return parse_body(response)


class LambdaHandlerOfClass(__LambdaHandler):
    @property
    def api_name(self) -> str:
        if "resource" in self.request_data:
            return self.request_data["resource"]
        elif self.business_handler.api_name and isinstance(
            self.business_handler.api_name, str
        ):
            return self.business_handler.api_name
        else:
            return self.business_handler.__name__

    def run(self):
        return self.business_handler(self.request_data, self.context).main()


class LambdaHandlerOfFunction(__LambdaHandler):
    @property
    def api_name(self) -> str:
        if "resource" in self.request_data:
            return self.request_data["resource"]
        else:
            return self.business_handler.__name__

    def run(self):
        return self.business_handler(self.request_data)
