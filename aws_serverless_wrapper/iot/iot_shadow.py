from .._helper import environ
from boto3 import client
from json import loads, dumps
from copy import deepcopy


__all__ = ["IoTShadowStatic"]


_iot_client = client("iot-data", region_name=environ["AWS_REGION"])


class IoTShadowStatic:
    def __init__(self, iot_device_name):
        self.__device_name = iot_device_name
        self.__reported = dict()
        self.__desired = dict()
        self.__delta = dict()
        self.__meta = dict()

        self.__fetch_timestamp = int()
        self.__version = int()

    @property
    def state(self):
        if not self.__fetch_timestamp:
            self.refresh()
        return deepcopy(self.__reported)

    @state.setter
    def state(self, new_state: dict):
        self.__set_new_desired_state(new_state)

    @state.deleter
    def state(self):
        self.__set_new_desired_state(dict())

    @property
    def desired(self):
        if not self.__fetch_timestamp:
            self.refresh()
        return deepcopy(self.__desired)

    @desired.setter
    def desired(self, new_state: dict):
        self.__set_new_desired_state(new_state)

    @property
    def delta(self):
        if not self.__fetch_timestamp:
            self.refresh()
        return deepcopy(self.__delta)

    @property
    def meta(self):
        if not self.__fetch_timestamp:
            self.refresh()
        return deepcopy(self.__meta)

    def refresh(self):
        response = _iot_client.get_thing_shadow(thingName=self.__device_name)
        payload_stream = response["payload"]
        payload = loads(payload_stream.read())

        self.__fetch_timestamp = payload["timestamp"]
        self.__version = payload["version"]
        self.__reported = (
            payload["state"]["reported"] if "reported" in payload["state"] else dict()
        )
        self.__desired = (
            payload["state"]["desired"] if "desired" in payload["state"] else dict()
        )
        self.__delta = (
            payload["state"]["delta"] if "delta" in payload["state"] else dict()
        )

        self.__meta = payload["metadata"]

    def __set_new_desired_state(self, new_state):
        if not isinstance(new_state, dict):
            raise TypeError("new desired state must be of type dict")

        response = _iot_client.update_thing_shadow(
            thingName=self.__device_name,
            payload=dumps({"state": {"desired": new_state}}),
        )

        if response == "SUCCESS":
            self.__reported.update(new_state)
