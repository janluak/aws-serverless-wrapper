from .json_to_python_type import json_to_python_type_switch
from json import load as json_load
from jsonschema.validators import Draft7Validator, RefResolver
from os.path import dirname, realpath
from aws_serverless_wrapper._helper import delete_keys_in_nested_dict

__current_validator = Draft7Validator

__all__ = [
    "get_schema",
    "get_validator",
    "verify_data",
    "check_if_data_type_is_allowed",
]


def __resolver(directory):
    absolute_directory = dirname(realpath(directory))

    relative_directory = f"file://{absolute_directory}/"

    return RefResolver(relative_directory, None)


def get_schema(file: str = None, url: str = None) -> dict:
    if file:
        if ".json" != file[-5:]:
            file += ".json"
        with open(file, "r") as f:
            return json_load(f)

    elif url:
        raise NotImplementedError

    else:
        raise ValueError("at least one input must be specified")


def get_validator(file: str = None, url: str = None, raw: dict = None, non_required=False):
    if not any(i for i in [file, url, raw]):
        raise ValueError("at least one input must be specified")

    if file or url:
        schema = get_schema(file=file, url=url)
    elif raw:
        schema = raw
    else:
        raise ValueError("at least one input must be specified")

    if non_required:
        delete_keys_in_nested_dict(schema, "required")

    if file:
        return __current_validator(schema, resolver=__resolver(file))
    elif url:
        return __current_validator(schema, resolver=None)
    else:
        return __current_validator(schema)


def verify_data(directory: str, data_to_verify: dict):
    """
    Verify data to JSON schema

    Parameters
    ----------
    directory : str
        where to get the schema from
        ``{{path/to/file | https://url.to.file}}``
    data_to_verify : dict
        any data to check if fitting the schema

    """
    validator = get_validator(directory)
    validator.validate(data_to_verify)


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
