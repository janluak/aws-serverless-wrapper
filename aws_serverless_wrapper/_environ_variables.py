from os import environ as os_environ
from json import load

__all__ = ["environ"]
required_environ_keys = ["STAGE"]
fallback_values = {
    "dict_hash_digest_size": 20,
    "dict_hash_ignore_keys": ["time_stamp", "timestamp"],
}


class NoExceptDict(dict):
    def __getitem__(self, item):
        return self.get(item, NoExceptDict())


def change_dict_to_no_except_dict(data):
    if isinstance(data, list):
        for i in range(len(data)):
            change_dict_to_no_except_dict(i)
    elif isinstance(data, dict):
        for key in data.copy():
            data[key] = change_dict_to_no_except_dict(data[key])
        data = NoExceptDict(data)
    return data


class Environ:
    def __init__(self):
        self.__config_file = str()
        self.__config = dict()
        self._load_config_from_file()
        self._schema = dict()

    def _load_config_from_file(self, file_name=None):
        try:
            self.__config_file = (
                os_environ["WRAPPER_CONFIG_FILE"] if not file_name else file_name
            )
            with open(self.__config_file, "r") as f:
                self.__config = change_dict_to_no_except_dict(load(f))
        except KeyError:
            self.__config_file = str()
            self.__config = dict()
            from warnings import warn

            warn("No WRAPPER_CONFIG_FILE specified", ResourceWarning)

    def __fallback(self, key):
        if (
            self.__config_file != os_environ["WRAPPER_CONFIG_FILE"]
            if "WRAPPER_CONFIG_FILE" in os_environ
            else False
        ):
            self._load_config_from_file()
            return self.__getitem__(key)
        elif key in fallback_values:
            return fallback_values[key]
        elif key in os_environ:
            return os_environ[key]
        elif self._schema and key in self._schema["properties"] and "default" in self._schema["properties"][key]:
            return self._schema["properties"][key]["default"]
        else:
            return NoExceptDict()

    def set_keys(self, new_keys: dict):
        if self._schema:
            validator(self._schema).validate(new_keys)

        self.__config.update(new_keys)

    def set_schema(self, schema: dict):
        from jsonschema import Draft7Validator as validator
        global validator
        self._schema = schema

    def __getitem__(self, key):
        if key not in required_environ_keys:
            try:
                if (value := self.__config[key]) != NoExceptDict():
                    return value
                else:
                    return self.__fallback(key)
            except KeyError:
                return self.__fallback(key)
        else:
            try:
                return os_environ[key]
            except KeyError:
                return NoExceptDict()

    def __setitem__(self, key, value):
        self.__config[key] = change_dict_to_no_except_dict(value)

    def __iter__(self):
        if "WRAPPER_CONFIG_FILE" in os_environ and self.__config_file != os_environ["WRAPPER_CONFIG_FILE"]:
            self._load_config_from_file()
        return self.__config.__iter__()

    def __contains__(self, item):
        return item in self.__config or item in os_environ


environ = Environ()
