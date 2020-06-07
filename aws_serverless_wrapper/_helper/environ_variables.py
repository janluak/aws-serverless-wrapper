from os import environ as os_environ

__all__ = ["environ"]
required_environ_keys = ["STAGE"]


class Environ:
    def __getitem__(self, key):
        try:
            return os_environ[key]
        except KeyError:
            if key in required_environ_keys:
                raise EnvironmentError(
                    f"{key} must be defined in os.environment"
                )
            return str()

    def __setitem__(self, key, value):
        os_environ[key] = value

    def __iter__(self):
        return os_environ.__iter__()


environ = Environ()
