from .base_class import ServerlessBaseClass
from types import FunctionType


def aws_serverless_wrapper(main):
    if isinstance(main, FunctionType):
        from .serverless_handler import LambdaHandlerOfFunction

        return LambdaHandlerOfFunction(main).wrap_lambda

    else:
        if issubclass(main, ServerlessBaseClass):
            from .serverless_handler import LambdaHandlerOfClass

            return LambdaHandlerOfClass(main).wrap_lambda

        else:
            raise TypeError(
                f"if given a class it must derive from aws_serverless_wrapper.{ServerlessBaseClass.__name__}"
            )
