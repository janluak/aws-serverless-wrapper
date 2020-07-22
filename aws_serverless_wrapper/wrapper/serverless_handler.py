from abc import ABC, abstractmethod
from .base_class import ServerlessBaseClass
from .._helper import environ
from jsonschema.exceptions import ValidationError
from datetime import datetime
from types import FunctionType


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
        self.api_name = str()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def _get_api_name(self) -> str:
        return str()

    def input_verification(self, event) -> (None, dict):
        if environ["API_INPUT_VERIFICATION"]:
            from ..schema_validation import APIDataValidator

            origin_type = environ["API_INPUT_VERIFICATION"]["SCHEMA_ORIGIN"]
            origin_value = environ["API_INPUT_VERIFICATION"]["SCHEMA_DIRECTORY"]

            if "/" == origin_value[-1]:
                origin_value += self._get_api_name()

            try:
                self.request_data = APIDataValidator(
                    event, **{origin_type: origin_value},
                ).data
            except (OSError, TypeError, ValidationError) as e:
                from .._helper import log_api_validation_error

                error_log_item = log_api_validation_error(e, event, self.context)

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

    def _log_error(self, exc):
        if "abstract class" in exc.args[0]:
            raise exc

        from .._helper import log_exception

        error_log_item = log_exception(exc, self.request_data, self.context)

        response = {
            "statusCode": 500,
            "body": "internal server error",
            "headers": {"Content-Type": "text/plain"},
        }

        if environ["ERROR_LOG"]["API_RESPONSE"]:
            response.update(
                {
                    "headers": {"Content-Type": "application/json"},
                    "body": {
                        "basic": "internal server error",
                        "error_log_item": error_log_item,
                    },
                }
            )

        return response

    def wrap_lambda(self, event, context) -> dict:
        METRICS["container_reusing_count"] += 1

        self.request_data = event
        self.context = context
        if bad_input_response := self.input_verification(self.request_data):
            return bad_input_response

        try:
            if response := self.run():
                return response
            else:
                return {"statusCode": 200}
        except Exception as e:
            return self._log_error(e)


class LambdaHandlerOfClass(__LambdaHandler):
    def _get_api_name(self) -> str:
        if self.business_handler.api_name and isinstance(
            self.business_handler.api_name, str
        ):
            self.api_name = self.business_handler.api_name
        else:
            self.api_name = self.business_handler.__name__
        return self.api_name

    def run(self):
        return self.business_handler(self.request_data, self.context).main()


class LambdaHandlerOfFunction(__LambdaHandler):
    def _get_api_name(self) -> str:
        self.api_name = self.business_handler.__name__
        return self.api_name

    def run(self):
        return self.business_handler(self.request_data)
