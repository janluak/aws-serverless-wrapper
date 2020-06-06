from os import environ as os_environ

if os_environ["WRAPPER_DATABASE"] == "DynamoDB":
    from .dynamo_db import *

# from .dynamo_db import *
