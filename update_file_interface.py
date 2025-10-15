from abc import ABC, abstractmethod

class UpdateFileInterface(ABC):
    @abstractmethod
    def upload_to_file(self, type: Type) -> None:
        pass
