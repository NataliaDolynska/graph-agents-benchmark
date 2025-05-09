import json
import re
from neo4j import GraphDatabase
from neo4j import GraphDatabase

from text_to_cypher_benchmark.src.utils.huggingface_data_loader import HuggingFaceDataLoader

def     populate_neo4j_from_huggingface(dataset_name, neo4j_uri="bolt://localhost:7687", neo4j_user="neo4j", neo4j_password="your_password"):
    """
    Populates Neo4j with data from a HuggingFace dataset.

    Args:
        dataset_name: The name of the HuggingFace dataset.
        neo4j_uri: The URI of the Neo4j database.
        neo4j_user: The username for the Neo4j database.
        neo4j_password: The password for the Neo4j database.
    """
    try:
        data_loader = HuggingFaceDataLoader(dataset_name)
        data = data_loader.get_data()

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:
            for index, row in data.iterrows():
                print("INIDE: {} ROW: {}".format(index, row))
                session.run("CREATE (n:Question {id: $id, text: $text})", id=index, text=row['question'])
                # session.run("CREATE (n:Answer {id: $id, text: $text})", id=index, text=row['answer'])
                session.run("""
                    MATCH (q:Question {id: $id})
                    MATCH (a:Answer {id: $id})
                    MERGE (q)-[:ANSWERS]->(a)
                """, id=index)

        print("Neo4j database populated successfully.")

    except Exception as e:
        print(f"Error populating Neo4j: {e}")
    finally:
        driver.close()

def populate_neo4j_from_csv(csv_filepath, neo4j_uri="bolt://localhost:7687", neo4j_user="neo4j", neo4j_password="your_password"):
    """Populates Neo4j with data from a CSV file containing schema information.

    Args:
        csv_filepath: The path to the CSV file.
        neo4j_uri: The URI of the Neo4j database.
        neo4j_user: The username for the Neo4j database.
        neo4j_password: The password for the Neo4j database.
    """
    try:
        with open(csv_filepath, 'r') as file:
            content = file.read()

        # Use regex to match the structured schema part enclosed in double quotes, accounting for escaped double quotes.
        match = re.search(r',"(.*?)"$', content, re.DOTALL)

        if not match:
            print("No structured schema found in CSV.")
            return

        schema_json = match.group(1).replace("""\\""", "\\")
        schema_data = json.loads(schema_json)

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

        with driver.session() as session:

            # Create Node labels and constraints (if applicable)
            for label, props in schema_data.get('node_props', {}).items():
                session.run(f"CREATE CONSTRAINT IF NOT EXISTS ON (n:{label}) ASSERT n.id IS UNIQUE)")

            # Create relationships
            for rel in schema_data.get('relationships', []):
                start_node = rel['start']
                end_node = rel['end']
                rel_type = rel['type']

                # Ensure start and end node labels exist and create them if not
                session.run(f"CREATE CONSTRAINT IF NOT EXISTS ON (n:{start_node}) ASSERT n.id IS UNIQUE)")
                session.run(f"CREATE CONSTRAINT IF NOT EXISTS ON (n:{end_node}) ASSERT n.id IS UNIQUE)")

                # Assuming there are properties to be used for matching in relationships
                session.run(f"""
                    MATCH (s:{start_node} {{id: $start_node_id}})
                    MATCH (e:{end_node} {{id: $end_node_id}})
                    MERGE (s)-[:{rel_type}]->(e)
                """, start_node_id = "start_node_value", end_node_id = "end_node_value")

        print("Neo4j database populated successfully.")
    except Exception as e:
        print(f"Error populating Neo4j: {e}")
    finally:
        driver.close()

