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
from text_to_cypher_benchmark.src.model_provider import ModelsProvider
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from text_to_cypher_benchmark.src.solutions.base import Solution
from text_to_cypher_benchmark.src.models import Frameworks
from text_to_cypher_benchmark.src.utils.neo4j_integration import Neo4jConnectionManager

logger = logging.getLogger(__name__)


class LangChainSolution(Solution):
    """LangChain implementation for text-to-Cypher conversion."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.chain: Optional[Runnable] = None
        self.graph: Optional[Neo4jGraph] = None

    def get_name(self) -> Frameworks:
        return Frameworks.LANGCHAIN

    def initialize(self, **kwargs) -> bool:
        """Initialize LangChain with Neo4j connection."""
        try:
            # Initialize Neo4j connection
            self.graph = Neo4jGraph(
                url=self.config.get("neo4j_uri", "bolt://localhost:7687"),
                username=self.config.get("neo4j_user", "neo4j"),
                password=self.config.get("neo4j_password", "password"),
            )

            print("1111")

            model_name = self.config["model_name"]

            print(f"Model name: {model_name}")
            llm, embed_model = ModelsProvider.provide(
                framework=self.get_name(),
                llm_model=model_name,
            )
            print("22222")
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
            print("333333")

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
        """Convert natural language question to Cypher query."""
        if not self.chain:
            raise ValueError("LangChain not initialized. Call initialize() first.")

        try:
            return self.chain.invoke(question)["result"]
        except Exception as e:
            logger.error(f"Failed to generate Cypher query: {e}")
            raise

    def close(self):
        """Clean up resources."""
        if self.graph:
            self.graph.close()
