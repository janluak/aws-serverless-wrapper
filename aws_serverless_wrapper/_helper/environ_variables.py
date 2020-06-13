from os import environ as os_environ
from json import load

__all__ = ["environ"]
required_environ_keys = ["STAGE", "WRAPPER_CONFIG_FILE"]
fallback_values = {
    "dict_hash_digest_size": 20,
    "dict_hash_ignore_keys": ["time_stamp", "timestamp"]
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
        self.__load_new_config()

    def __load_new_config(self):
        try:
            self.__config_file = os_environ["WRAPPER_CONFIG_FILE"]
            with open(self.__config_file, "r") as f:
                self.__config = change_dict_to_no_except_dict(load(f))
        except KeyError:
            self.__config_file = str()
            self.__config = dict()
            return str()

    def __fallback(self, key):
        if self.__config_file != os_environ["WRAPPER_CONFIG_FILE"]:
            self.__load_new_config()
            return self.__getitem__(key)
        elif key in fallback_values:
            return fallback_values[key]
        else:
            return NoExceptDict()

    def __getitem__(self, key):
        if key not in required_environ_keys:
            try:
                if value := self.__config[key]:
                    return value
                else:
                    return self.__fallback(key)
            except KeyError:
                return self.__fallback(key)
        else:
            try:
                return os_environ[key]
            except KeyError:
                raise EnvironmentError(
                    f"{key} must be defined in os.environment"
                )

    def __setitem__(self, key, value):
        self.__config[key] = value

    def __iter__(self):
        if self.__config_file != os_environ["WRAPPER_CONFIG_FILE"]:
            self.__load_new_config()
        return self.__config.__iter__()


environ = Environ()
