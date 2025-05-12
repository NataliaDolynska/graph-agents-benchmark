import asyncio
from typing import Optional

from langchain_neo4j import Neo4jGraph
from llama_index.llms.vertex import Vertex
from llama_index.core.settings import Settings
from llama_index.core import StorageContext
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
from llama_index.embeddings.vertex import VertexTextEmbedding
import vertexai
from google.oauth2 import service_account
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from graph_agents_benchmark.src.model_provider import ModelsProvider
from llama_index.core.agent.react import ReActAgent
from llama_index.tools.neo4j import Neo4jQueryToolSpec
from graph_agents_benchmark.src.models import Frameworks
from graph_agents_benchmark.src.solutions.base import Solution

import time
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os


class LlamaIndexSolution(Solution):
    """
    LlamaIndex implementation for text-to-Cypher conversion.

    Leverages LlamaIndex's capabilities to connect to Neo4j, construct prompts, and execute queries.
    """

    def __init__(
        self,
        model_name: str,
        db_user: str,
        db_password: str,
        db_url: str,
        db_name: Optional[str] = None,
    ):
        """
        Initializes the LlamaIndex solution with a configuration.

        Args:
            model_name (str): The name of the LLM model to use.
            db_user (str): The Neo4j database user.
            db_password (str): The Neo4j database password.
            db_url (str): The Neo4j database URL.
            db_name (Optional[str]): The Neo4j database name.
        """
        print(f"Initiating LlamaIndexSolution")
        self.llm = llm, self.embed_model = ModelsProvider.provide(
            self.get_name(), model_name
        )

        gds_db = Neo4jQueryToolSpec(
            url=db_url,
            user=db_user,
            password=db_password,
            llm=self.llm,
            validate_cypher=True,
            database=db_name,
        )

        tools = gds_db.to_tool_list()

        self.agent = ReActAgent.from_tools(
            tools=tools,
            llm=llm,
        )

    def get_name(self):
        """
        Returns the name of the solution.

        Returns:
            Frameworks: The name of the solution (LLAMA_INDEX).
        """
        return Frameworks.LLAMA_INDEX

    def predict(self, question: str) -> str:
        """
        Converts a natural language question to a Cypher query using LlamaIndex.

        Args:
            question (str): The input question in natural language.

        Returns:
            str: The generated Cypher query.
        """
        print(f"Question : {question}")
        return str(self.agent.chat(message=question))
