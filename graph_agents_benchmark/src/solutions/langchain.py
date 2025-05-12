import logging
from typing import Optional, Dict, Any
from langchain_neo4j import Neo4jGraph
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from graph_agents_benchmark.src.model_provider import ModelsProvider
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from graph_agents_benchmark.src.solutions.base import Solution
from graph_agents_benchmark.src.models import Frameworks
from graph_agents_benchmark.src.utils.neo4j_integration import Neo4jConnectionManager

logger = logging.getLogger(__name__)


class LangChainSolution(Solution):
    """
    LangChain implementation for text-to-Cypher conversion.

    Leverages LangChain's capabilities to connect to Neo4j, construct prompts, and execute queries.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the LangChain solution with a configuration.

        Args:
            config (Optional[Dict[str, Any]]): A dictionary containing configuration parameters, such as Neo4j connection details and model settings.
        """
        super().__init__()
        self.config = config or {}
        self.chain: Optional[Runnable] = None
        self.graph: Optional[Neo4jGraph] = None

    def get_name(self) -> Frameworks:
        """
        Returns the name of the solution.

        Returns:
            Frameworks: The name of the solution (LANGCHAIN).
        """
        return Frameworks.LANGCHAIN

    def initialize(self, **kwargs) -> bool:
        """
        Initializes the LangChain solution by establishing a connection to Neo4j and creating the LLM chain.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Initialize Neo4j connection
            self.graph = Neo4jGraph(
                url=self.config.get("neo4j_uri", "bolt://localhost:7687"),
                username=self.config.get("neo4j_user", "neo4j"),
                password=self.config.get("neo4j_password", "password"),
            )

            model_name = self.config["model_name"]

            print(f"Model name: {model_name}")
            llm, embed_model = ModelsProvider.provide(
                framework=self.get_name(),
                llm_model=model_name,
            )
            self.llm = llm
            self.embed_model = embed_model
            # Initialize LLM

            # Create prompt template
            # prompt = ChatPromptTemplate.from_messages(
            #     [
            #         SystemMessage(
            #             content="You are a helpful assistant that converts natural language to Cypher queries for Neo4j."
            #         ),
            #         HumanMessage(content="Convert this question to Cypher: {question}"),
            #     ]
            # )
            # Create chain
            self.chain = GraphCypherQAChain.from_llm(
                self.llm,
                graph=self.graph,
                verbose=True,
                # use_function_response=True,
                allow_dangerous_requests=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {e}")
            return False

    def predict(self, question: str) -> str:
        """
        Converts a natural language question to a Cypher query using LangChain.

        Args:
            question (str): The input question in natural language.

        Returns:
            str: The generated Cypher query.

        Raises:
            ValueError: If LangChain is not initialized.
            Exception: If Cypher query generation fails.
        """
        if not self.chain:
            raise ValueError("LangChain not initialized. Call initialize() first.")

        try:
            return self.chain.invoke(question)["result"]
        except Exception as e:
            logger.error(f"Failed to generate Cypher query: {e}")
            raise

    def close(self):
        """
        Closes the connection to Neo4j.
        """
        if self.graph:
            self.graph.close()
