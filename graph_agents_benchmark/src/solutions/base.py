from abc import ABC, abstractmethod
from graph_agents_benchmark.src.models import Frameworks


class Solution(ABC):
    """
    Abstract base class for text-to-Cypher solutions.

    Defines the interface for all text-to-Cypher solutions, including methods for setup, prediction, and teardown.
    """

    def before(self) -> None:
        """
        Optional method to perform any setup actions before prediction.
        """
        pass

    @abstractmethod
    def get_name(self) -> Frameworks:
        """
        Returns the name of the solution.

        Returns:
            Frameworks: The name of the solution.
        """
        pass

    @abstractmethod
    def predict(self, question: str) -> str:
        """
        Predicts the Cypher query for a given question.

        Args:
            question (str): The input question.

        Returns:
            str: The predicted Cypher query.
        """
        pass

    def after(self) -> None:
        """
        Optional method to perform any teardown actions after prediction.
        """
        pass
