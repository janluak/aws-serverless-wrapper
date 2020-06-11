from aws_serverless_wrapper._helper import environ

if environ["WRAPPER_DATABASE"]["MODEL"] == "DynamoDB":
    from .dynamo_db import *
