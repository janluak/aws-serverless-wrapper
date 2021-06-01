class AWSFakeContext:
    def __init__(self, aws_request_id, log_group_name, function_name, function_version):
        self.aws_request_id = (aws_request_id,)
        self.log_group_name = log_group_name
        self.function_name = function_name
        self.function_version = function_version

    aws_request_id = "uuid"
    log_group_name = "test/log/group"
    function_name = "test_function"
    function_version = "$LATEST"


fake_context = AWSFakeContext
