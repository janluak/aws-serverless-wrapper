from abc import ABC, abstractmethod
from inspect import stack
from jsonschema.exceptions import ValidationError
from ..._helper import environ
from ...schema_validation import SchemaValidator


class AttributeExistsException(AttributeError):
    pass


class AttributeNotExistsException(AttributeError):
    pass


class CustomExceptionRaiser:
    def __init__(self, table):
        self.table = table

    def not_found_message(self, not_found_item):
        raise FileNotFoundError(
            {
                "statusCode": 404,
                "body": f"{not_found_item} not found in {self.table.name}",
                "headers": {"Content-Type": "text/plain"},
            }
        )

    def _primary_key_rudimentary_message(self, provided_message):
        raise LookupError(
            {
                "statusCode": 400,
                "body": f"Wrong primary for {self.table.name}: "
                f"required for table is {self.table.pk}; {provided_message}",
                "headers": {"Content-Type": "text/plain"},
            }
        )

    def missing_primary_key(self, missing):
        raise self._primary_key_rudimentary_message(f"missing {missing}")

    def wrong_primary_key(self, given):
        raise self._primary_key_rudimentary_message(f"given {given}")

    def wrong_data_type(self, error: ValidationError):
        if error.validator == "type":
            response = {
                "statusCode": 415,
                "body": f"Wrong value type in {self.table.name} for key={'/'.join(error.absolute_path)}:\n"
                f"{error.message}.",
                "headers": {"Content-Type": "text/plain"},
            }
            if "enum" in error.schema and error.schema["enum"]:
                response["body"] += f"\nenum: {error.schema['enum']}"
        elif error.validator == "required":
            response = {
                "statusCode": 400,
                "body": f"{error.message} for table {self.table.name} and is missing",
                "headers": {"Content-Type": "text/plain"},
            }
        elif error.validator == "additionalProperties":
            response = {
                "statusCode": 400,
                "body": f"{error.message} for table {self.table.name}\n"
                f"path to unexpected property: {list(error.relative_path)}",
                "headers": {"Content-Type": "text/plain"},
            }
        else:
            response = {
                "statusCode": 500,
                "body": f"unexpected database validation error for table {self.table.name}: {error.message}",
                "headers": {"Content-Type": "text/plain"},
            }

        raise TypeError(response)

    def item_already_existing(self, item):
        raise FileExistsError(
            {
                "statusCode": 409,
                "body": f"Item is already existing.\nTable: {self.table.name}\nItem: {item}",
                "headers": {"Content-Type": "text/plain"},
            }
        )


class NoSQLTable(ABC):
    @abstractmethod
    def __init__(self, table_name):
        self.__table_name = table_name
        self.__custom_exception_raiser = CustomExceptionRaiser(self)

        self.__schema_validator = SchemaValidator(
            **{
                environ["WRAPPER_DATABASE"]["noSQL"]["SCHEMA_ORIGIN"].lower(): environ[
                    "WRAPPER_DATABASE"
                ]["noSQL"]["SCHEMA_DIRECTORY"]
                + self.__table_name
            }
        )

    @property
    def name(self):
        return self.__table_name

    @property
    def pk(self):
        return self.__schema_validator.schema["default"]

    @property
    def schema(self):
        return self.__schema_validator.schema

    @property
    @abstractmethod
    def table(self):
        pass

    @property
    def custom_exception(self):
        return self.__custom_exception_raiser

    def _validate_input(self, given_input):
        if "update" in stack()[1].function:
            try:
                self.__schema_validator.validate_sub_part(given_input)
            except ValidationError as e:
                self.custom_exception.wrong_data_type(e)

        elif "put" == stack()[1].function:
            try:
                self.__schema_validator.validate(given_input)
            except ValidationError as e:
                self.custom_exception.wrong_data_type(e)

        else:
            self._primary_key_checker(given_input)

    def _primary_key_checker(self, given_primaries):
        if not all(pk in given_primaries for pk in self.pk):
            self.custom_exception.missing_primary_key(
                [key for key in self.pk if key not in given_primaries]
            )
        elif len(given_primaries) > len(self.pk):
            self.custom_exception.wrong_primary_key(given_primaries)

    @abstractmethod
    def describe(self) -> dict:
        pass

    @abstractmethod
    def get(self, **primary_dict):
        pass

    @abstractmethod
    def add_new_attribute(
        self,
        new_data: dict,
        update_if_existent=False,
        create_item_if_non_existent=False,
        **primary_dict,
    ):
        pass

    @abstractmethod
    def update_attribute(
        self,
        new_data,
        set_new_attribute_if_not_existent=False,
        create_item_if_non_existent=False,
        **primary_dict,
    ):
        pass

    @abstractmethod
    def update_list_item(self, primary_dict, item_no, new_data):
        pass

    @abstractmethod
    def update_append_list(
        self,
        new_data,
        set_new_attribute_if_not_existent=False,
        create_item_if_non_existent=False,
        **primary_dict,
    ):
        pass

    @abstractmethod
    def update_increment(self, path_of_to_increment: dict, **primary_dict):
        pass

    @abstractmethod
    def put(self, item: dict, overwrite=False):
        pass

    @abstractmethod
    def remove_attribute(self, path_of_attribute: dict, **primary_dict):
        pass

    @abstractmethod
    def remove_entry_in_list(
        self, path_to_list: dict, position_to_delete: int, **primary_dict
    ):
        pass

    @abstractmethod
    def delete(self, **primary_dict) -> None:
        pass

    @abstractmethod
    def get_and_delete(self, **primary_dict) -> dict:
        pass

    @abstractmethod
    def scan(self) -> dict:
        pass

    @abstractmethod
    def truncate(self) -> dict:
        pass
