from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from warnings import catch_warnings, simplefilter


def test_get_undefined_os_environ_mandatory():
    if "WRAPPER_CONFIG_FILE" in os_environ:
        del os_environ["WRAPPER_CONFIG_FILE"]

    with catch_warnings(record=True) as w:
        simplefilter("always")

        from aws_serverless_wrapper._environ_variables import Environ

        environ = Environ()

        assert environ["unknown_entry"] == dict()

        assert issubclass(w[0].category, ResourceWarning)
        assert "No WRAPPER_CONFIG_FILE specified" == str(w[0].message)


class TestEnvironVariables(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"


class TestEmptyEnviron(TestEnvironVariables):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        os_environ[
            "WRAPPER_CONFIG_FILE"
        ] = f"{dirname(realpath(__file__))}/_helper_wrapper_config_empty.json"

    def test_get_unknown_key(self):
        from aws_serverless_wrapper._environ_variables import environ

        self.assertEqual(dict(), environ["unknown_key"])

    def test_get_fallback_from_os_environ(self):

        os_environ["SOME_OS_ENVIRON_KEY"] = "SOME_VALUE"

        from aws_serverless_wrapper._environ_variables import environ
        self.assertEqual(os_environ["SOME_OS_ENVIRON_KEY"], environ["SOME_OS_ENVIRON_KEY"])

    def test_get_fallback_from_os_environ_with_prio(self):
        os_environ["SOME_OS_ENVIRON_KEY"] = "SOME_VALUE"

        from aws_serverless_wrapper._environ_variables import environ
        self.assertEqual(os_environ["SOME_OS_ENVIRON_KEY"], environ["SOME_OS_ENVIRON_KEY"])

    def test_set_and_get_entry(self):
        from aws_serverless_wrapper._environ_variables import environ

        self.assertEqual(dict(), environ["new_key"])
        environ["new_key"] = "new_value"
        self.assertEqual("new_value", environ["new_key"])

    def test_set_no_except_dict(self):
        from aws_serverless_wrapper._environ_variables import environ

        self.assertEqual(dict(), environ["new_dict"])
        environ["new_dict"] = {"key1": {"key1.1": "value1"}, "key2": "value2"}
        self.assertEqual("value1", environ["new_dict"]["key1"]["key1.1"])

        from aws_serverless_wrapper._environ_variables import NoExceptDict

        empty_entry = environ["new_dict"]["key1"]["unknown_key"]
        self.assertIsInstance(empty_entry, NoExceptDict)
        self.assertEqual(empty_entry, dict())


class TestConfiguredEnviron(TestEnvironVariables):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        os_environ[
            "WRAPPER_CONFIG_FILE"
        ] = f"{dirname(realpath(__file__))}/_helper_wrapper_config.json"

    def test_get_stage(self):
        from aws_serverless_wrapper._environ_variables import environ

        self.assertEqual(os_environ["STAGE"], environ["STAGE"])

    def test_get_key_as_in_config_file(self):
        from aws_serverless_wrapper._environ_variables import environ

        self.assertEqual(environ["key1"], "value1")

    def test_check_if_key_in_environ(self):
        from aws_serverless_wrapper._environ_variables import environ

        if "key1" not in environ:
            self.fail("key1 not found in environ")

    def test_get_if_key_in_sub_environ_key(self):
        from aws_serverless_wrapper._environ_variables import environ

        if "key3.1" in environ["key3"]:
            pass
        else:
            self.fail("not found existing key key3.1 in key3")

    def test_check_if_key_in_sub_environ_key(self):
        from aws_serverless_wrapper._environ_variables import environ

        if "key3.2" not in environ["key3"]:
            pass
        else:
            self.fail("found non existing key key3.2 in key3")

    def test_check_for_keys_in_non_existent_sub_environ_key(self):
        from aws_serverless_wrapper._environ_variables import environ

        if "key3.2.1" in environ["key3"]["key3.2"]:
            self.fail("found non existing key key3.2.1 in key3/key3.2")
        else:
            pass

    def test_get_unknown_key_depth_1(self):
        from aws_serverless_wrapper._environ_variables import environ

        try:
            value = environ["unknown1"]
        except Exception as e:
            self.fail(f"some exception was raised: {e}")

        if "unknown1" in environ:
            self.fail("found level 1")

    def test_get_unknown_key_depth_2(self):
        from aws_serverless_wrapper._environ_variables import environ

        try:
            value = environ["unknown1"]["unknown2"]
        except Exception as e:
            self.fail(f"some exception was raised: {e}")

        if "unknown2" in environ["unknown1"]:
            self.fail("found level 2")

    def test_get_unknown_key_depth_3(self):
        from aws_serverless_wrapper._environ_variables import environ

        try:
            value = environ["unknown1"]["unknown2"]["unknown3"]
        except Exception as e:
            self.fail(f"some exception was raised: {e}")

        if "unknown3" in environ["unknown1"]["unknown2"]:
            self.fail("found level 3")

    def test_set_additional_keys(self):
        from aws_serverless_wrapper._environ_variables import environ

        new_keys = {
            "new_key1": "some_value",
            "bool_key": True
        }

        environ.set_keys(new_keys)

        self.assertEqual(
            new_keys["new_key1"],
            environ["new_key1"]
        )

        self.assertEqual(
            new_keys["bool_key"],
            environ["bool_key"]
        )

    def test_key_in_environ(self):
        from aws_serverless_wrapper._environ_variables import environ

        new_keys = {
            "new_key1": "some_value",
            "bool_key": True
        }

        environ.set_keys(new_keys)

        self.assertIn("new_key1", environ)
        self.assertIn("STAGE", environ)
        self.assertNotIn("unknown_entry", environ)


class TestConfiguredEnvironFromSchema(TestConfiguredEnviron):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "schema for environ and it's keys",
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "key1": {
                "type": "string"
            },
            "key2": {
                "type": "integer"
            },
            "key3": {
                "type": "object"
            },
            "bool_key": {
                "type": "boolean"
            },
            "int_key": {
                "type": "integer",
                "default": 3
            }
        }
    }

    def test_set_schema(self):
        from aws_serverless_wrapper._environ_variables import environ

        environ.set_schema(self.schema)

        self.assertEqual(self.schema, environ._schema)

    def test_invalid_updated_key(self):
        from jsonschema import ValidationError
        from aws_serverless_wrapper._environ_variables import environ
        environ.set_schema(self.schema)

        environ.set_keys(
            {
                "bool_key": True
            }
        )

        with self.assertRaises(ValidationError):
            environ.set_keys(
                {
                    "bool_key": "True"
                }
            )

    def test_get_from_default(self):
        from aws_serverless_wrapper._environ_variables import environ
        environ.set_schema(self.schema)

        self.assertEqual(self.schema["properties"]["int_key"]["default"], environ["int_key"])
