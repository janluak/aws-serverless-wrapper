import logging
from abc import ABC, abstractmethod
from .base_class import ServerlessBaseClass
from ._environ_variables import environ
from jsonschema.exceptions import ValidationError
from datetime import datetime
from types import FunctionType
from ._body_parsing import parse_body, ParsingError
from json import load, dumps
from os.path import dirname, realpath

with open(f"{dirname(realpath(__file__))}/wrapper_config_schema.json", "r") as wrapper_config_schema:
    environ.set_schema(load(wrapper_config_schema))

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
        self, business_handler: (ServerlessBaseClass.__subclasses__(), FunctionType),
        **config
    ):
        self.business_handler = business_handler
        self.request_data = None
        self.context = None

        if config:
            environ.set_keys(config)

    @abstractmethod
    def run(self):
        pass

    @property
    @abstractmethod
    def api_name(self) -> str:
        return str()

    def input_verification(self) -> (None, dict):
        try:
            if environ["API_INPUT_VERIFICATION"]:
                from aws_schema import APIDataValidator

                origin_type = environ["API_INPUT_VERIFICATION"]["SCHEMA_ORIGIN"]
                origin_value = environ["API_INPUT_VERIFICATION"]["SCHEMA_DIRECTORY"]

                self.request_data = APIDataValidator(
                    self.request_data, self.api_name, **{origin_type: origin_value},
                ).data
        except (OSError, TypeError, ValidationError, ValueError) as e:
            from .error_logging import log_api_validation_error

            error_log_item = log_api_validation_error(e, self.request_data, self.context)

            if not error_log_item:
                return e.args[0]

            else:
                try:
                    statusCode = e.args[0]["statusCode"]
                except (KeyError, TypeError):
                    statusCode = 400
                return {
                    "statusCode": statusCode,
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
                return_error_in_response=environ["API_RESPONSE_VERIFICATION"]["RETURN_INTERNAL_SERVER_ERROR"],
                **{origin_type: origin_value},
            )

    def _log_error(self, exc):
        if "abstract class" in exc.args[0]:
            raise exc

        if environ["ERROR_LOG"]["API_RESPONSE"]:
            from .error_logging import log_exception

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
        self.context = context
        if environ["LOG_RAW_EVENT"]:
            logging.info(f"raw event: {event}")

        if "headers" in event:
            event["headers"] = {k.lower(): v for k, v in event["headers"].items()}

        encoding = "utf-8"
        if "headers" in event and "content-type" in event["headers"]:
            if ";" in event["headers"]["content-type"]:
                event["headers"]["content-type"], encoding = event["headers"]["content-type"].split(";")
                encoding = encoding.split("=")[-1]

        try:
            if environ["PARSE_BODY"] and environ["PARSE_REQUEST_BODY"]:
                event = parse_body(event, encoding)
                if environ["LOG_PARSED_EVENT"]:
                    logging.info(f"parsed event: {dumps(event)}")

            self.request_data = event
            if response := self.input_verification():
                pass
            else:
                if response := self.run():
                    self.output_verification(response)
                else:
                    response = {"statusCode": 200}
        except (ParsingError, NotImplementedError) as e:
            if isinstance(e, NotImplementedError):
                from .error_logging import log_exception
                log_exception(e, self.request_data, self.context)
            response = e.args[0]
        except Exception as e:
            response = self._log_error(e)

        if environ["PARSE_BODY"] and environ["PARSE_RESPONSE_BODY"]:
            if environ["LOG_PRE_PARSED_RESPONSE"]:
                logging.info(f"pre parsed response: {dumps(response)}")
            try:
                response = parse_body(response)
            except NotImplementedError as e:
                from .error_logging import log_exception
                log_exception(e, self.request_data, self.context)
                response = e.args[0]

        if environ["LOG_RAW_RESPONSE"]:
            logging.info(f"raw response: {dumps(response)}")
        return response


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
        if not environ["with_context"]:
            return self.business_handler(self.request_data)
        else:
            return self.business_handler(self.request_data, self.context)
