from abc import ABC, abstractmethod


class ServerlessBaseClass(ABC):
    def __init__(self, event: dict, context: object) -> (None, dict):
        self.__event = event
        self.__context = context

    @property
    def event(self):
        return self.__event

    @property
    def context(self):
        return self.__context

    @abstractmethod
    def main(self) -> dict:
        return {"statusCode": 200}

    @classmethod
    @property
    def api_name(cls) -> str:
        return str()
