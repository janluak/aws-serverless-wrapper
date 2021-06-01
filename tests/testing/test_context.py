def test_fake_context():
    from aws_serverless_wrapper.testing import fake_context
    from aws_serverless_wrapper.testing.context import AWSFakeContext

    context = AWSFakeContext(
        aws_request_id="uuid",
        log_group_name="test/log/group",
        function_name="test_function",
        function_version="$LATEST",
    )

    assert dir(fake_context) == dir(context)
    assert fake_context.aws_request_id == "uuid"
