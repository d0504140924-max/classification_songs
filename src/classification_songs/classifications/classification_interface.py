from abc import ABC, abstractmethod
from classification_songs.configorations._dataclasses import Types
class ClassificationInterface(ABC):
    @abstractmethod
    def comparison_type(self)->Types:
        pass