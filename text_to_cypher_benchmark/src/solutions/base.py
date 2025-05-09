from abc import ABC, abstractmethod
from text_to_cypher_benchmark.src.models import Frameworks


class Solution(ABC):
    """Abstract base class for text-to-Cypher solutions."""

    @abstractmethod
    def get_name(self) -> Frameworks:
        pass

    @abstractmethod
    def predict(self, question: str) -> str:
        """Predicts the Cypher query for a given question."""
        pass

