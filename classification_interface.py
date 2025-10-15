from abc import ABC, abstractmethod

class ClassificationInterface(ABC):
    @abstractmethod
    def comparison_type(self, file_info: FileInfo)->Type:
        pass