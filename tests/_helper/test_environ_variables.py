from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
import pytest


def test_get_undefined_os_environ_mandatory():
    with pytest.raises(KeyError):
        from aws_serverless_wrapper._helper import environ


class TestEnvironVariables(TestCase):
    actual_cwd = str()

    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config_empty.json"
        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

    def test_get_stage(self):
        from aws_serverless_wrapper._helper import environ

        self.assertEqual(os_environ["STAGE"], environ["STAGE"])

    def test_get_from_new_config_file(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        self.assertEqual(environ["key1"], "value1")

    def test_check_if_key_in_environ(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        if "key1" not in environ:
            self.fail("key1 not found in environ")

    def test_get_if_key_in_sub_environ_key(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        if "key3.1" in environ["key3"]:
            pass
        else:
            self.fail("not found existing key key3.1 in key3")

    def test_check_if_key_in_sub_environ_key(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        if "key3.2" not in environ["key3"]:
            pass
        else:
            self.fail("found non existing key key3.2 in key3")

    def test_check_for_keys_in_non_existent_sub_environ_key(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        if "key3.2.1" in environ["key3"]["key3.2"]:
            self.fail("found non existing key key3.2.1 in key3/key3.2")
        else:
            pass

    def test_get_unknown_key_depth_1(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        try:
            value = environ["unknown1"]
        except Exception as e:
            self.fail(f"some exception was raised: {e}")

        if "unknown1" in environ:
            self.fail("found level 1")

    def test_get_unknown_key_depth_2(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        try:
            value = environ["unknown1"]["unknown2"]
        except Exception as e:
            self.fail(f"some exception was raised: {e}")

        if "unknown2" in environ["unknown1"]:
            self.fail("found level 2")

    def test_get_unknown_key_depth_3(self):
        os_environ["WRAPPER_CONFIG_FILE"] = "_helper_wrapper_config.json"
        from aws_serverless_wrapper._helper import environ

        try:
            value = environ["unknown1"]["unknown2"]["unknown3"]
        except Exception as e:
            self.fail(f"some exception was raised: {e}")

        if "unknown3" in environ["unknown1"]["unknown2"]:
            self.fail("found level 3")