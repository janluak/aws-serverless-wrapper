from abc import ABC, abstractmethod
from .schema_validator import SchemaValidator
from jsonschema.exceptions import ValidationError


class DataValidator(ABC):
    def __init__(
        self, data_to_verify: dict, file: str = None, url: str = None, raw: dict = None
    ):

        self.__data = data_to_verify

        file = self.__craft_full_origin(file)
        url = self.__craft_full_origin(url)

        try:
            self.__schema_validator = SchemaValidator(file, url, raw)
        except FileNotFoundError:
            raise EnvironmentError(
                {
                    "statusCode": 501,
                    "body": "API is not defined",
                    "headers": {"Content-Type": "text/plain"},
                }
            )

    @property
    def schema(self):
        return self.__schema_validator.schema

    @property
    def data(self):
        return self.__data

    @property
    @abstractmethod
    def httpMethod(self) -> str:
        return str()

    @staticmethod
    @abstractmethod
    def handle_exception(validation_error):
        pass

    def __craft_full_origin(self, origin):
        if origin:
            if origin[-1] == "/":
                origin = self.__insert_api_name_to_origin(origin)

            return self.insert_specifics_to_origin(origin)

    @abstractmethod
    def insert_specifics_to_origin(self, origin: str) -> str:
        return str()

    @staticmethod
    def __insert_api_name_to_origin(origin):
        from inspect import stack

        parent_function = stack()[4][3]

        origin += parent_function

        return origin

    def verify(self):
        try:
            self.__schema_validator.validate(self.__data)
        except ValidationError as err:
            self.handle_exception(err)
