from .._helper import environ


if environ["WRAPPER_DATABASE"]["MODEL"] == "DynamoDB":
    from .dynamo_db import Table
else:
    class Table:
        pass
