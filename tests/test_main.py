from glob import glob


def test_all_config_files_in_test_directory():
    from aws_serverless_wrapper.__main__ import check_wrapper_config

    config_files = glob("./**/[!_]*wrapper_config.json", recursive=True)

    for config_file in config_files:
        check_wrapper_config(config_file)
