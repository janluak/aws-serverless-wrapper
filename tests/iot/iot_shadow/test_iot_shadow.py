from boto3 import client
from moto import mock_iot, mock_iotdata
from freezegun import freeze_time
from os.path import dirname, realpath
import json
from pytest import fixture


test_thing_name = "TestThing"
test_state = {"test_key": "test_value"}


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
        payload=json.dumps({"state": {"reported": test_state}}),
    )

    from aws_serverless_wrapper.iot.iot_shadow import IoTShadowStatic

    iot_shadow = IoTShadowStatic(test_thing_name)
    assert iot_shadow.state == test_state


@mock_iotdata
def test_set_shadow(iot_shadow_config):

    from aws_serverless_wrapper.iot.iot_shadow import IoTShadowStatic

    iot_shadow = IoTShadowStatic(test_thing_name)
    iot_shadow.state = test_state

    assert iot_shadow.desired == test_state

    iot_client = client("iot-data", region_name=environ["AWS_REGION"])
    payload = json.loads(
        iot_client.get_thing_shadow(thingName=test_thing_name)["payload"].read()
    )

    assert payload["state"]["desired"] == test_state
    assert payload["state"]["delta"] == test_state
    assert iot_shadow.delta == test_state


@mock_iotdata
@freeze_time("2020-01-01")
def test_get_shadow_meta(iot_shadow_config):

    from aws_serverless_wrapper.iot.iot_shadow import IoTShadowStatic

    iot_shadow = IoTShadowStatic(test_thing_name)
    iot_shadow.state = test_state

    assert iot_shadow.meta == {"desired": {"test_key": {"timestamp": 1577836800}}}


@mock_iotdata
def test_updated_shadow(iot_shadow_config):

    from aws_serverless_wrapper.iot.iot_shadow import IoTShadowStatic

    iot_shadow = IoTShadowStatic(test_thing_name)
    iot_shadow.state = test_state

    assert iot_shadow.desired == test_state

    iot_client = client("iot-data", region_name=environ["AWS_REGION"])
    iot_client.update_thing_shadow(
        thingName=test_thing_name,
        payload=json.dumps({"state": {"reported": {"test_key": "new_test_value"}}}),
    )

    assert iot_shadow.state != {"test_key": "new_test_value"}

    iot_shadow.refresh()
    assert iot_shadow.state == {"test_key": "new_test_value"}


@mock_iotdata
@freeze_time("2020-01-01")
def test_unchangeable_properties(iot_shadow_config):
    from aws_serverless_wrapper.iot.iot_shadow import IoTShadowStatic

    iot_shadow = IoTShadowStatic(test_thing_name)
    iot_shadow.state = test_state

    state = iot_shadow.state
    state["test_key"] = "changed_test_value_state"
    assert state != iot_shadow.state

    desired = iot_shadow.desired
    desired["test_key"] = "changed_test_value_desired"
    assert desired != iot_shadow.desired

    delta = iot_shadow.delta
    delta["test_key"] = "changed_test_value_delta"
    assert delta != iot_shadow.delta

    meta = iot_shadow.meta
    meta["desired"]["test_key"]["timestamp"] = 123
    assert meta != iot_shadow.meta
