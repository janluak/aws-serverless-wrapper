class Namespace:
    """Simple object for storing attributes.

    Implements equality by attribute names and values, and provides a simple
    string representation.

    Copied from argparse.ArgumentParser
    """

    def __init__(self, **kwargs):
        for name in kwargs:
            setattr(self, name, kwargs[name])

    def __eq__(self, other):
        if not isinstance(other, Namespace):
            return NotImplemented
        return vars(self) == vars(other)

    def __contains__(self, key):
        return key in self.__dict__


context = Namespace(
    **{
        "aws_request_id": "uuid",
        "log_group_name": "test/log/group",
        "function_name": "test_function",
    }
)
