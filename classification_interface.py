from abc import ABC, abstractmethod

class ClassificationInterface(ABC):
    @abstractmethod
    def comparison_type(self)->Type:
        pass