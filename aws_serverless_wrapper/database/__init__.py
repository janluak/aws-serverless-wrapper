from aws_serverless_wrapper._helper import environ

if environ["WRAPPER_DATABASE"] == "DynamoDB":
    from .dynamo_db import *
