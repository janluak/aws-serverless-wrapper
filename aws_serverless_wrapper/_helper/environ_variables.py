from os import environ as os_environ
from json import load

__all__ = ["environ"]
required_environ_keys = ["STAGE", "WRAPPER_CONFIG_FILE"]


class Environ:
    def __init__(self):
        self.__load_new_config()

    def __load_new_config(self):
        try:
            self.__config_file = os_environ["WRAPPER_CONFIG_FILE"]
            with open(self.__config_file, "r") as f:
                self.__config = load(f)
        except KeyError:
            self.__config_file = str()
            self.__config = dict()
            return str()

    def __getitem__(self, key):
        try:
            return self.__config[key]
        except KeyError:
            if key in required_environ_keys:
                raise EnvironmentError(
                    f"{key} must be defined in os.environment"
                )
            if self.__config_file != os_environ["WRAPPER_CONFIG_FILE"]:
                self.__load_new_config()
                return self.__getitem__(key)
            else:
                return str()

    def __setitem__(self, key, value):
        self.__config[key] = value

    def __iter__(self):
        return self.__config.__iter__()


environ = Environ()
