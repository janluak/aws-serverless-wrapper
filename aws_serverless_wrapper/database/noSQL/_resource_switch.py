from ..._helper import environ


if environ["WRAPPER_DATABASE"]["noSQL"]["MODEL"] == "DynamoDB":
    from .dynamo_db import Table
else:
    from ._base_class import NoSQLTable as Table
