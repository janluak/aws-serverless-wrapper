import logging
from ._validation_base_class import DataValidator
from .._helper import environ

logger = logging.getLogger("API Response Check")

__all__ = ["ResponseDataValidator"]


class ResponseDataValidator(DataValidator):
    def __init__(
        self,
        response_data: dict,
        httpMethod: str,
        file: str = None,
        url: str = None,
        raw: dict = None,
    ):
        self.__httpMethod = httpMethod
        try:
            super().__init__(response_data, file, url, raw)
            self.verify()
        except EnvironmentError:
            exception_text = f"no specified response schema available for statusCode 418\nresponse: {response_data}"
            if environ["API_RESPONSE_VERIFICATION"]["RETURN_INTERNAL_SERVER_ERROR"]:
                raise EnvironmentError(
                    {
                        "statusCode": 501,
                        "body": exception_text,
                        "headers": {"Content-Type": "text/plain"},
                    }
                )
            else:
                logger.warning(exception_text)

    @property
    def httpMethod(self) -> str:
        return self.__httpMethod

    @property
    def statusCode(self) -> str:
        return str(self.data["statusCode"])

    def insert_specifics_to_origin(self, origin: str) -> str:
        if self.httpMethod not in origin:
            if ".json" == origin[-5:]:
                origin = origin[:-5]

            origin += "-" + self.httpMethod + "-" + self.statusCode + ".json"

        elif self.statusCode not in origin:
            if ".json" == origin[-5:]:
                origin = origin[:-5]

            origin += "-" + self.statusCode + ".json"

        return origin

    @staticmethod
    def handle_exception(validation_error):
        if environ["API_RESPONSE_VERIFICATION"]["RETURN_INTERNAL_SERVER_ERROR"]:
            raise TypeError(
                {
                    "statusCode": 500,
                    "body": {
                        "invalid response": validation_error.instance,
                        "schema context": validation_error.context.__str__(),
                    },
                }
            )
        else:
            logger.warning(f"invalid response:\n\n{validation_error.instance}")
