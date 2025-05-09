from typing import List, Dict, Tuple, Optional
import json
from pathlib import Path
from text_to_cypher_benchmark.src.utils.neo4j_integration import Neo4jConnectionManager
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuestionAnswerPair:
    question: str
    cypher: str
    difficulty: str = "medium"  # easy/medium/hard

class FlightAccidentLoader:
    """Loader for flight accident knowledge graph dataset."""

    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.qa_pairs: List[QuestionAnswerPair] = []

    def load_and_validate(self) -> bool:
        """Load and validate the dataset file."""
        try:
            with open(self.data_path, 'r') as f:
                self.data = json.load(f)

            # Validate schema
            required_sections = {'schema', 'entities'}
            if not required_sections.issubset(self.data.keys()):
                missing = required_sections - set(self.data.keys())
                raise ValueError(f"Missing required sections: {missing}")

            return True

        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            return False

    def generate_qa_pairs(self) -> List[QuestionAnswerPair]:
        """Generate diverse question-answer pairs from the dataset."""
        if not hasattr(self, 'data'):
            raise ValueError("Dataset not loaded. Call load_and_validate() first.")

        # Basic questions
        self.qa_pairs.extend([
            QuestionAnswerPair(
                "How many flight accidents are there?",
                "MATCH (a:FlightAccident) RETURN count(a)",
                "easy"
            ),
            QuestionAnswerPair(
                "List flight accidents with more than 50 deaths",
                "MATCH (a:FlightAccident) WHERE a.number_of_deaths > 50 RETURN a",
                "medium"
            )
        ])

        # Relationship-based questions
        if 'relations' in self.data.get('schema', {}):
            self.qa_pairs.append(
                QuestionAnswerPair(
                    "Show accidents involving Boeing aircraft",
                    """MATCH (a:FlightAccident)-[:involves]->(m:AircraftModel)
                       WHERE m.name CONTAINS 'Boeing'
                       RETURN a""",
                    "hard"
                )
            )

        return self.qa_pairs

    def populate_neo4j(self, neo4j_manager: Neo4jConnectionManager) -> bool:
        """Populate Neo4j with the dataset entities and relationships."""
        try:
            # Create nodes
            for entity in self.data.get('entities', []):
                neo4j_manager.create_node(
                    label=entity.get('label'),
                    properties=entity.get('properties', {})
                )

            # Create relationships
            for rel in self.data.get('schema', {}).get('relations', []):
                neo4j_manager.create_relationship(
                    source_label=rel.get('subj_label'),
                    source_props={},
                    rel_type=rel.get('label'),
                    target_label=rel.get('obj_label'),
                    target_props={}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to populate Neo4j: {e}")
            return False