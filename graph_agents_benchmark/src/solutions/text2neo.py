from graph_agents_benchmark.src.models import Frameworks
from graph_agents_benchmark.src.solutions.base import Solution
from rag_cmd.src.core.agent import Agent
from rag_cmd.src.adapter.neo4j_sample import Neo4JSampleAdapter
from rag_cmd.src.db.db_provider import DBProvider
import os
from typing import Optional


class Text2NeoSolution(Solution):
    """
    Custom implementation for text-to-Cypher conversion.

    Leverages a custom agent and Neo4j adapter to generate Cypher queries.
    """

    def get_name(self):
        """
        Returns the name of the solution.

        Returns:
            Frameworks: The name of the solution (CUSTOM).
        """
        return Frameworks.CUSTOM

    def __init__(self, model_name: str, db_user: str = None, db_password: str = None, db_url: str = None,
                 db_name: Optional[str] = None):
        """
        Initializes the Text2Neo solution with a configuration.

        Args:
            model_name (str): The name of the LLM model to use (not directly used in this implementation).
            db_user (str, optional): The Neo4j database user. Defaults to the environment variable NEO4J_USER.
            db_password (str, optional): The Neo4j database password. Defaults to the environment variable NEO4J_PASSWORD.
            db_url (str, optional): The Neo4j database URL. Defaults to the environment variable NEO4J_URI.
            db_name (str, optional): The Neo4j database name. Defaults to the environment variable NEO4J_DATABASE.
        """
        db_user = db_user or os.environ.get("NEO4J_USER")
        db_password = db_password or os.environ.get("NEO4J_PASSWORD")
        db_url = db_url or os.environ.get("NEO4J_URI")
        db_name = db_name or os.environ.get("NEO4J_DATABASE")

        self.db_provider = DBProvider(db_url, db_user, db_password, db_name)
        self.agent = Agent(
            system_description=["You are a helpful assistant that answers questions about a Neo4j database."],
            db_provider=self.db_provider)
        self.neo4j_adapter = Neo4JSampleAdapter(self.agent, self.db_provider)

    def predict(self, question: str) -> str:
        """
        Converts a natural language question to a Cypher query using a custom agent and Neo4j adapter.

        Args:
            question (str): The input question in natural language.

        Returns:
            str: The generated Cypher query.
        """
        try:
            result, cached = self.agent.execute_command(
                command_name='neo4j_cypher_query_examples',
                arguments={},
            )
            return result
        except Exception as e:
            return str(e)
