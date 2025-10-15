from abc import ABC, abstractmethod


class GetInfoInterface(ABC):

    @abstractmethod
    def get_info(self, path: str) ->FileInfo:
        pass