from json import loads, JSONDecodeError
from ._validation_base_class import DataValidator


__all__ = ["APIDataValidator"]


class APIDataValidator(DataValidator):
    def __init__(
        self, api_data: dict, file: str = None, url: str = None, raw: dict = None
    ):
        super().__init__(api_data, file, url, raw)

        if self.httpMethod != "nonHTTP":
            self.__convert_none_to_empty_dict()
            self.__rename_multi_value_query_to_query_param()

        self.__decode_json_body()

        self.verify()

    @property
    def httpMethod(self) -> str:
        return self.data["httpMethod"] if "httpMethod" in self.data else "nonHTTP"

    def insert_specifics_to_origin(self, origin: str) -> str:
        if self.httpMethod not in origin:
            if ".json" == origin[-5:]:
                origin = origin[:-5]

            origin += "-" + self.httpMethod + ".json"

        return origin

    def __convert_none_to_empty_dict(self):
        # for json_schema validator not able to process type(None)
        for key in ["body", "pathParameters", "multiValueQueryStringParameters"]:
            try:
                if isinstance(self.data[key], type(None)):
                    self.data[key] = dict()
            except KeyError:
                pass

    def __rename_multi_value_query_to_query_param(self):
        self.data["queryParameters"] = (
            self.data["multiValueQueryStringParameters"]
            if "multiValueQueryStringParameters" in self.data
            else dict()
        )

    def __decode_json_body(self):
        if "body" in self.data and not isinstance(self.data["body"], dict):
            try:
                self.data["body"] = loads(self.data["body"])
            except (JSONDecodeError, TypeError):
                raise TypeError(
                    {
                        "statusCode": 400,
                        "body": "Body has to be json formatted",
                        "headers": {"Content-Type": "text/plain"},
                    }
                )

    @staticmethod
    def handle_exception(validation_error):
        raise TypeError(
            {
                "statusCode": 400
                if (
                    len(validation_error.path) == 0
                    or "httpMethod" != validation_error.path[0]
                )
                else 405,
                "body": validation_error.message
                if len(validation_error.__str__().split("\n")) > 12
                else validation_error.__str__(),
                "headers": {"Content-Type": "text/plain"},
            }
        )
