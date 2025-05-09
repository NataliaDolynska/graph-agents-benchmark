from text_to_cypher_benchmark.src.models import Frameworks
from text_to_cypher_benchmark.src.solutions.base import Solution
from rag_cmd.src.core.agent import Agent
from rag_cmd.src.adapter.neo4j_sample import Neo4JSampleAdapter
from rag_cmd.src.db.db_provider import DBProvider
import os
from typing import Optional


class Text2NeoSolution(Solution):

    def get_name(self):
        return Frameworks.CUSTOM

    def __init__(self, model_name: str, db_user: str = None, db_password: str = None, db_url: str = None,
                 db_name: Optional[str] = None):
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
        try:
            result, cached = self.agent.execute_command(
                command_name='neo4j_cypher_query_examples',
                arguments={},
            )
            return result
        except Exception as e:
            return str(e)
