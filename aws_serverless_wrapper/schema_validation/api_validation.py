from json import loads, JSONDecodeError
from .schema_validator import SchemaValidator
from jsonschema.exceptions import ValidationError


__all__ = ["APIDataValidator"]


class APIDataValidator:
    def __init__(
        self,
        api_data: dict,
        file: str = None,
        url: str = None,
        raw: dict = None,
        json_formatted_body: bool = False,
    ):
        self.__httpMethod = api_data["httpMethod"]

        file = self.__craft_full_origin(file)
        url = self.__craft_full_origin(url)

        try:
            self.__schema_validator = SchemaValidator(file, url, raw)
        except FileNotFoundError:
            raise EnvironmentError(
                {
                    "statusCode": 501,
                    "body": "API is not defined",
                    "headers": {"Content-Type": "text/plain"},
                }
            )
        self.__data = api_data

        self.__convert_none_to_empty_dict()
        self.__rename_multi_value_query_to_query_param()

        if json_formatted_body:
            self.__decode_json_body()

        self.__verify()

    @property
    def schema(self):
        return self.__schema_validator.schema

    @property
    def data(self):
        return self.__data

    def __craft_full_origin(self, origin):
        if origin:
            if origin[-1] == "/":
                origin = self.__insert_api_name_to_origin(origin)

            return self.__insert_http_method_to_origin(origin)

    @staticmethod
    def __insert_api_name_to_origin(origin):
        from inspect import stack

        parent_function = stack()[3][3]

        origin += parent_function

        return origin

    def __insert_http_method_to_origin(self, origin):
        if self.__httpMethod not in origin:
            if ".json" == origin[-5:]:
                origin = origin[:-5]

            origin += "-" + self.__httpMethod + ".json"

        return origin

    def __check_for_required_parameter_types(self):
        for key in self.schema["required"]:
            if key not in self.__data:
                raise TypeError(
                    {
                        "statusCode": 400,
                        "body": f"{key} has to be included",
                        "headers": {"Content-Type": "text/plain"},
                    }
                )

    def __convert_none_to_empty_dict(self):
        # for json_schema validator not able to process type(None)
        for key in ["body", "pathParameters", "multiValueQueryStringParameters"]:
            try:
                if isinstance(self.__data[key], type(None)):
                    self.__data[key] = dict()
            except KeyError:
                pass

    def __rename_multi_value_query_to_query_param(self):
        self.__data["queryParameters"] = (
            self.__data["multiValueQueryStringParameters"]
            if "multiValueQueryStringParameters" in self.__data
            else dict()
        )

    def __decode_json_body(self):
        try:
            self.__data["body"] = loads(self.__data["body"])
        except (JSONDecodeError, TypeError):
            raise TypeError(
                {
                    "statusCode": 400,
                    "body": "Body has to be json formatted",
                    "headers": {"Content-Type": "text/plain"},
                }
            )

    def __verify(self):
        self.__check_for_required_parameter_types()

        try:
            self.__schema_validator.validate(self.__data)
        except ValidationError as err:
            raise TypeError(
                {
                    "statusCode": 400
                    if (len(err.path) == 0 or "httpMethod" != err.path[0])
                    else 405,
                    "body": err.__str__(),
                    "headers": {"Content-Type": "text/plain"},
                }
            )
