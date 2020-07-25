from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from copy import deepcopy
from hashlib import blake2b
from json import dumps

reference_dict = {
    "some_string": "abcdef",
    "some_int": 42,
    "some_float": 13.42,
    "some_dict": {"key1": "value1", "key2": 2},
    "some_nested_dict": {"KEY1": {"subKEY1": "subVALUE1", "subKEY2": 42.24}},
    "some_array": [
        "array_string",
        13,
        {"KEY1": {"arraySubKEY1": "subVALUE1", "arraySubKEY2": 42.24}},
    ],
}


class TestNestedDict(TestCase):
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

    def setUp(self) -> None:
        self._reference_dict = deepcopy(reference_dict)

    def tearDown(self) -> None:
        global reference_dict
        reference_dict = self._reference_dict


class TestDeleteKeysInNestedDict(TestNestedDict):
    def test_delete_nothing(self):
        from aws_serverless_wrapper._helper.nested_dict import (
            delete_keys_in_nested_dict,
        )

        self.assertEqual(reference_dict, delete_keys_in_nested_dict(reference_dict, []))

    def test_delete_top_level(self):
        from aws_serverless_wrapper._helper.nested_dict import (
            delete_keys_in_nested_dict,
        )

        to_deleted_dict = deepcopy(reference_dict)
        delete_keys_in_nested_dict(to_deleted_dict, ["some_float"])

        reference_dict.pop("some_float")

        self.assertEqual(reference_dict, to_deleted_dict)

    def test_delete_in_sub_dict(self):
        from aws_serverless_wrapper._helper.nested_dict import (
            delete_keys_in_nested_dict,
        )

        to_deleted_dict = deepcopy(reference_dict)
        delete_keys_in_nested_dict(to_deleted_dict, ["subKEY1"])

        reference_dict["some_nested_dict"]["KEY1"].pop("subKEY1")

        self.assertEqual(reference_dict, to_deleted_dict)

    def test_delete_in_array_contained_dict(self):
        from aws_serverless_wrapper._helper.nested_dict import (
            delete_keys_in_nested_dict,
        )

        to_deleted_dict = deepcopy(reference_dict)
        delete_keys_in_nested_dict(to_deleted_dict, ["arraySubKEY1"])

        reference_dict["some_array"][2]["KEY1"].pop("arraySubKEY1")

        self.assertEqual(reference_dict, to_deleted_dict)


class TestHashDict(TestNestedDict):
    def test_unchanged_dict(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        reference_hash = blake2b(
            str.encode(dumps(reference_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertEqual(reference_hash, hash_dict(reference_dict))

    def test_deleted_keys_dict(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = ["some_string"]
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict.pop("some_string")

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertEqual(reference_hash, hash_dict(reference_dict))

    def test_changed_origin_string(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict["some_string"] = "changed_string"

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertNotEqual(reference_hash, hash_dict(reference_dict))

    def test_changed_origin_int(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict["some_int"] += 3

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertNotEqual(reference_hash, hash_dict(reference_dict))

    def test_changed_origin_float(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict["some_float"] += 3.59

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertNotEqual(reference_hash, hash_dict(reference_dict))

    def test_changed_sub_dict(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict["some_dict"]["key1"] = "changed_value"

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertNotEqual(reference_hash, hash_dict(reference_dict))

    def test_changed_nested_dict(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict["some_nested_dict"]["KEY1"]["subKEY2"] += 15.324

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertNotEqual(reference_hash, hash_dict(reference_dict))

    def test_changed_array(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict["some_array"][1] += 15

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertNotEqual(reference_hash, hash_dict(reference_dict))

    def test_changed_nested_dict_in_array(self):
        from aws_serverless_wrapper._helper.environ_variables import environ
        from aws_serverless_wrapper._helper.nested_dict import hash_dict

        environ["dict_hash_ignore_keys"] = []
        environ["dict_hash_digest_size"] = 20

        expected_dict = deepcopy(reference_dict)
        expected_dict["some_array"][2]["KEY1"]["arraySubKEY2"] += 139

        reference_hash = blake2b(
            str.encode(dumps(expected_dict, sort_keys=True)),
            digest_size=environ["dict_hash_digest_size"],
        ).hexdigest()

        self.assertNotEqual(reference_hash, hash_dict(reference_dict))


class TestUpdateNestedDict(TestNestedDict):
    def test_update_nested_key_reassignment(self):

        from aws_serverless_wrapper._helper import update_nested_dict

        origin_dict = deepcopy(reference_dict)
        verify_dict = deepcopy(reference_dict)

        verify_dict["some_nested_dict"]["KEY1"]["subKEY1"] = "new Value"

        origin_dict = update_nested_dict(
            origin_dict, {"some_nested_dict": {"KEY1": {"subKEY1": "new Value"}}}
        )
        assert origin_dict == verify_dict
        assert origin_dict["some_dict"] == verify_dict["some_dict"]

    def test_update_nested_key_mutable(self):

        from aws_serverless_wrapper._helper import update_nested_dict

        origin_dict = deepcopy(reference_dict)
        verify_dict = deepcopy(reference_dict)

        verify_dict["some_nested_dict"]["KEY1"]["subKEY1"] = "new Value"

        update_nested_dict(
            origin_dict, {"some_nested_dict": {"KEY1": {"subKEY1": "new Value"}}}
        )
        assert origin_dict == verify_dict
        assert origin_dict["some_dict"] == verify_dict["some_dict"]
