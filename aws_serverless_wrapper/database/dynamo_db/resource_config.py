from os import environ as os_environ

__all__ = ["resource_config"]
__db_aws_region = "eu-central-1"


def craft_config():
    __switch_local_docker_env = {
        "UnitTest": "http://localhost:8000",
        "AWS_SAM_LOCAL": "http://docker.for.mac.localhost:8000",
    }
    __switch_db_resource_config = {
        "local": {
            "endpoint_url": __switch_local_docker_env[
                "UnitTest" if "AWS_SAM_LOCAL" not in os_environ else "AWS_SAM_LOCAL"
            ],
            "region_name": "dummy",
            "aws_access_key_id": "dummy",
            "aws_secret_access_key": "dummy",
        },
        "cloud": {"region_name": __db_aws_region},
    }

    if "AWS_SAM_LOCAL" in os_environ:
        os_environ["ENV"] = "local"
        os_environ["STAGE"] = "TEST"
    elif "AWS_LAMBDA_FUNCTION_NAME" in os_environ:
        os_environ["ENV"] = "cloud"
    elif "UnitTest" in os_environ:
        os_environ["ENV"] = "local"
        os_environ["STAGE"] = "TEST"
    else:
        if not all(key in os_environ for key in ["STAGE", "ENV"]):
            raise ValueError("'STAGE' and 'ENV' need to be provided in os.environ")
        # else:
        #     env = os_environ["ENV"]

    return __switch_db_resource_config[os_environ["ENV"]]


resource_config = craft_config()
