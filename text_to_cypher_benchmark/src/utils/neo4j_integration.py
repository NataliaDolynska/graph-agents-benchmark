from __future__ import annotations
from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase, BoltDriver, Transaction, Result
from neo4j.exceptions import Neo4jError
import os
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

class Neo4jConnectionManager:
    """Manages Neo4j database connections with connection pooling and retry logic."""

    def __init__(self,
                 uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                 user: str = os.getenv("NEO4J_USER", "neo4j"),
                 password: str = os.getenv("NEO4J_PASSWORD", "password"),
                 max_connection_pool_size: int = 50,
                 connection_timeout: int = 30):
        self._driver: BoltDriver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=max_connection_pool_size,
            connection_timeout=connection_timeout
        )
        self._verify_connectivity()

    def _verify_connectivity(self) -> None:
        """Verify the database connection is working."""
        try:
            self._driver.verify_connectivity()
        except Exception as e:
            logger.error("Failed to connect to Neo4j: %s", e)
            raise

    @contextmanager
    def session(self, **kwargs) -> Transaction:
        """Provide a transactional context for database operations."""
        with self._driver.session(**kwargs) as session:
            try:
                yield session
            except Neo4jError as e:
                logger.error("Neo4j operation failed: %s", e)
                raise
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                raise

    def execute_query(self,
                     query: str,
                     parameters: Optional[Dict[str, Any]] = None,
                     **kwargs) -> List[Dict[str, Any]]:
        """
        Execute a parameterized Cypher query with automatic retry.

        Args:
            query: Cypher query string
            parameters: Dictionary of query parameters
            kwargs: Additional session configuration options

        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}
        with self.session(**kwargs) as session:
            result: Result = session.run(query, parameters)
            return [dict(record) for record in result]

    def create_node(self,
                   label: str,
                   properties: Dict[str, Any],
                   **kwargs) -> Dict[str, Any]:
        """
        Create a node with MERGE to prevent duplicates.

        Args:
            label: Node label
            properties: Node properties

        Returns:
            Created node properties
        """
        query = (
            f"MERGE (n:{label} $props) "
            "RETURN n { .* }"
        )
        result = self.execute_query(query, {"props": properties}, **kwargs)
        return result[0] if result else {}

    def create_relationship(self,
                           source_label: str,
                           source_props: Dict[str, Any],
                           rel_type: str,
                           target_label: str,
                           target_props: Dict[str, Any],
                           rel_props: Optional[Dict[str, Any]] = None,
                           **kwargs) -> Dict[str, Any]:
        """
        Create a relationship between nodes using MERGE for both nodes and relationship.

        Args:
            source_label: Source node label
            source_props: Source node properties
            rel_type: Relationship type
            target_label: Target node label
            target_props: Target node properties
            rel_props: Relationship properties

        Returns:
            Created relationship properties
        """
        query = (
            f"MERGE (a:{source_label} $source_props) "
            f"MERGE (b:{target_label} $target_props) "
            f"MERGE (a)-[r:{rel_type} $rel_props]->(b) "
            "RETURN r { .* }"
        )
        params = {
            "source_props": source_props,
            "target_props": target_props,
            "rel_props": rel_props or {}
        }
        result = self.execute_query(query, params, **kwargs)
        return result[0] if result else {}

    def get_indexes(self) -> List[Dict[str, Any]]:
        """Get list of all indexes in the database."""
        query = "SHOW INDEXES"
        return self.execute_query(query)

    def close(self) -> None:
        """Close all database connections."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connections closed")

    def __enter__(self) -> Neo4jConnectionManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
