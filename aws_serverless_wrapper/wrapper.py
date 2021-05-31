from .base_class import ServerlessBaseClass
from types import FunctionType
from functools import wraps, partial

__all__ = ["aws_serverless_wrapper"]


def aws_serverless_wrapper(main=None, **config):
    if main is None:
        return partial(aws_serverless_wrapper, **config)

    @wraps(main)
    def wrapper(event, context):
        if isinstance(main, FunctionType):
            from .serverless_handler import LambdaHandlerOfFunction

            return LambdaHandlerOfFunction(main, **config).wrap_lambda(event, context)

        else:
            if issubclass(main, ServerlessBaseClass):
                from .serverless_handler import LambdaHandlerOfClass

                return LambdaHandlerOfClass(main, **config).wrap_lambda(event, context)

            else:
                raise TypeError(
                    f"if given a class it must derive from aws_serverless_wrapper.{ServerlessBaseClass.__name__}"
                )
    return wrapper
