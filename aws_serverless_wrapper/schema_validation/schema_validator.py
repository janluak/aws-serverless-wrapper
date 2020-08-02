from .json_to_python_type import json_to_python_type_switch
from json import load as json_load
from jsonschema.validators import Draft7Validator, RefResolver
from os.path import dirname, abspath
from .._helper import delete_keys_in_nested_dict
from copy import deepcopy

_current_validator = Draft7Validator

__all__ = [
    "SchemaValidator",
    "verify_data",
    "check_if_data_type_is_allowed",
]


class SchemaValidator:
    def __init__(self, file: str = None, url: str = None, raw: dict = None):
        if not any(i for i in [file, url, raw]):
            raise ValueError("one input must be specified")
        self.__file = file
        self.__url = url
        self.__raw = raw

        self.__resolver = None

        self.__validator = None
        self.__validator_without_required_check = None

        if file:
            if ".json" != file[-5:]:
                file += ".json"
            with open(file, "r") as f:
                self.__raw_schema = json_load(f)

        elif url:
            raise NotImplementedError

        else:
            self.__raw_schema = raw

    @property
    def schema(self):
        return self.validator.schema

    @property
    def validator(self):
        if not self.__validator:
            self.__create_validator()
        return self.__validator

    @property
    def validator_without_required_check(self):
        if not self.__validator_without_required_check:
            self.__create_validator(no_required_key=True)
        return self.__validator_without_required_check

    def validate(self, data, no_required_check=False):
        if not no_required_check:
            self.validator.validate(data)
        else:
            self.validator_without_required_check.validate(data)

    def __file_resolver(self):
        absolute_directory = dirname(abspath(self.__file))
        relative_directory = f"file://{absolute_directory}/"
        self.__resolver = RefResolver(relative_directory, None)

    def __url_resolver(self):
        raise NotImplementedError

    def __create_validator(self, no_required_key=False):
        if self.__file:
            self.__file_resolver()
        elif self.__url:
            self.__url_resolver()

        if no_required_key:
            schema = deepcopy(self.__raw_schema)
            delete_keys_in_nested_dict(schema, "required")
            self.__validator_without_required_check = _current_validator(
                schema, resolver=self.__resolver
            )
        else:
            self.__validator = _current_validator(
                self.__raw_schema, resolver=self.__resolver
            )


def verify_data(
    data_to_verify: dict, file: str = None, url: str = None, raw: dict = None
):
    """
    Verify data to JSON schema

    Parameters
    ----------
    data_to_verify : dict
        any data to check if fitting the schema
    file : str
        if schema is originated at file
    url : str
        if schema is originated at url
    raw : dict
        the schema directly provided

    """
    validator_class = SchemaValidator(file, url, raw)
    validator_class.validator.validate(data_to_verify)


def check_if_data_type_is_allowed(data, json_type, enum=False):
    if enum:
        if data not in enum:
            raise TypeError
    else:
        if not isinstance(json_type, (list, tuple)):
            json_type = [json_type]

        for type_entry in json_type:
            if isinstance(data, json_to_python_type_switch[type_entry]):
                return
        raise TypeError
