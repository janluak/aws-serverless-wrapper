from boto3 import client
from moto import mock_iot, mock_iotdata
from freezegun import freeze_time
from os.path import dirname, realpath
import json
from pytest import fixture

test_thing_name = "TestThing"
simple_test_state = {"test_key": "new_test_value"}
complex_test_state = {
    "level1": {"level2a": {"key1": 1, "key2": 2}, "level2b": {"key1": 1, "key2": 2}}
}


@mock_iotdata
def echo_desired_as_reported():
    iot_client = client("iot-data", region_name=environ["AWS_REGION"])
    payload = json.loads(
        iot_client.get_thing_shadow(thingName=test_thing_name)["payload"].read()
    )
    desire = payload["state"]["desired"]
    iot_client.update_thing_shadow(
        thingName=test_thing_name,
        payload=json.dumps({"state": {"reported": desire, "desired": desire}}),
    )


@fixture
@mock_iot
def iot_shadow_config():
    from aws_serverless_wrapper._helper import environ

    global environ
    environ._load_config_from_file(
        f"{dirname(realpath(__file__))}/iot_shadow_wrapper_config.json"
    )

    iot_raw_client = client("iot", region_name=environ["AWS_REGION"])
    iot_raw_client.create_thing(thingName=test_thing_name)


@mock_iotdata
def test_get_shadow(iot_shadow_config):
    iot_client = client("iot-data", region_name=environ["AWS_REGION"])
    iot_client.update_thing_shadow(
        thingName=test_thing_name,
        payload=json.dumps({"state": {"reported": complex_test_state}}),
    )

    from aws_serverless_wrapper.iot.iot_shadow_handler import IoTShadowStaticHandler

    iot_shadow = IoTShadowStaticHandler(test_thing_name)
    assert iot_shadow.reported == complex_test_state


@mock_iotdata
def test_set_shadow(iot_shadow_config):
    from aws_serverless_wrapper.iot.iot_shadow_handler import IoTShadowStaticHandler

    iot_shadow = IoTShadowStaticHandler(test_thing_name)
    iot_shadow.desired = complex_test_state

    assert iot_shadow.desired == complex_test_state

    iot_client = client("iot-data", region_name=environ["AWS_REGION"])
    payload = json.loads(
        iot_client.get_thing_shadow(thingName=test_thing_name)["payload"].read()
    )

    assert payload["state"]["desired"] == complex_test_state
    assert payload["state"]["delta"] == complex_test_state

    assert iot_shadow.delta != complex_test_state
    iot_shadow.refresh()
    assert iot_shadow.delta == complex_test_state


@mock_iotdata
@freeze_time("2020-01-01")
def test_get_shadow_meta(iot_shadow_config):
    from aws_serverless_wrapper.iot.iot_shadow_handler import IoTShadowStaticHandler

    iot_shadow = IoTShadowStaticHandler(test_thing_name)
    iot_shadow.desired = complex_test_state

    assert iot_shadow.meta == {
        "desired": {
            "level1": {
                "level2a": {
                    "key1": {"timestamp": 1577836800},
                    "key2": {"timestamp": 1577836800},
                },
                "level2b": {
                    "key1": {"timestamp": 1577836800},
                    "key2": {"timestamp": 1577836800},
                },
            }
        }
    }


@mock_iotdata
def test_foreign_updated_shadow(iot_shadow_config):
    from aws_serverless_wrapper.iot.iot_shadow_handler import IoTShadowStaticHandler

    iot_shadow = IoTShadowStaticHandler(test_thing_name)
    iot_shadow.desired = simple_test_state

    assert iot_shadow.desired == simple_test_state

    iot_client = client("iot-data", region_name=environ["AWS_REGION"])
    iot_client.update_thing_shadow(
        thingName=test_thing_name,
        payload=json.dumps({"state": {"reported": {"test_key": "new_test_value"}}}),
    )

    assert iot_shadow.reported != {"test_key": "new_test_value"}

    iot_shadow.refresh()
    assert iot_shadow.reported == {"test_key": "new_test_value"}


@mock_iotdata
@freeze_time("2020-01-01")
def test_unchangeable_properties(iot_shadow_config):
    from aws_serverless_wrapper.iot.iot_shadow_handler import IoTShadowStaticHandler

    iot_shadow = IoTShadowStaticHandler(test_thing_name)
    iot_shadow.desired = simple_test_state

    state = iot_shadow.reported
    state["test_key"] = "changed_test_value_state"
    assert state != iot_shadow.reported

    desired = iot_shadow.desired
    desired["test_key"] = "changed_test_value_desired"
    assert desired != iot_shadow.desired

    delta = iot_shadow.delta
    delta["test_key"] = "changed_test_value_delta"
    assert delta != iot_shadow.delta

    meta = iot_shadow.meta
    meta["desired"]["test_key"]["timestamp"] = 123
    assert meta != iot_shadow.meta


@mock_iotdata
def test_set_desired_and_retrieve_reported(iot_shadow_config):
    from aws_serverless_wrapper.iot.iot_shadow_handler import IoTShadowStaticHandler

    iot_shadow = IoTShadowStaticHandler(test_thing_name)
    iot_shadow.desired = complex_test_state
    iot_shadow.refresh()

    assert iot_shadow.delta == complex_test_state

    echo_desired_as_reported()
    iot_shadow.refresh()

    assert iot_shadow.reported == complex_test_state


@mock_iotdata
@freeze_time()
def test_update_part_of_state(iot_shadow_config):
    from aws_serverless_wrapper.iot.iot_shadow_handler import IoTShadowStaticHandler

    updated_complex_state = {
        "level1": {
            "level2a": {"key1": 1, "key2": "new_value"},
            "level2b": {"key1": 1, "key2": 2},
        }
    }

    iot_shadow = IoTShadowStaticHandler(test_thing_name)
    iot_shadow.desired = complex_test_state

    assert iot_shadow.desired == complex_test_state
    echo_desired_as_reported()
    iot_shadow.refresh()
    assert iot_shadow.reported == complex_test_state

    iot_shadow.update({"level1": {"level2a": {"key2": "new_value"}}})

    assert iot_shadow.desired == updated_complex_state
    assert iot_shadow.reported != updated_complex_state
    echo_desired_as_reported()
    iot_shadow.refresh()
    assert iot_shadow.reported == updated_complex_state
