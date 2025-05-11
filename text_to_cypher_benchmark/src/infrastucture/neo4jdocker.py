import os
import time
from typing import Optional

from python_on_whales import DockerClient

from neo4j import GraphDatabase

from text_to_cypher_benchmark.src.settings import ROOT_DIR


class Neo4jComposeRunner:
    def __init__(
            self,
            db_name: str,
            user: str = "neo4j",
            password: str = "neo4j_test_password",
            compose_file: Optional[str] = "docker-compose.yaml",
    ):
        self._db_name = db_name
        self._user = user
        self._password = password
        self._uri = "bolt://localhost:7687"
        self._compose_file = compose_file
        self._started = False

        compose_file_path = os.path.join(ROOT_DIR, self._compose_file)
        if not os.path.exists(compose_file_path):
            raise FileNotFoundError("There is no compose file at {}".format(compose_file_path))
        self._docker = DockerClient(compose_files=[])

    def start(self):
        print(f"🟢 Starting Neo4j with database '{self._db_name}' using {self._compose_file}...")
        os.environ["NEO4J_DB"] = self._db_name
        self._docker.compose.up(detach=True)
        self._wait_for_neo4j_ready()

    def stop(self):
        print("🛑 Stopping Neo4j Compose setup...")
        self._docker.compose.down()

    def _wait_for_neo4j_ready(self, retries=30, delay=2):
        print("⏳ Waiting for Neo4j to become ready via Bolt...")
        for attempt in range(1, retries + 1):
            try:
                driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
                with driver.session(database=self._db_name) as session:
                    session.run("RETURN 1")
                print("✅ Neo4j is ready.")
                self._started = True
                return
            except Exception as e:
                print(f"🔁 Attempt {attempt}: {e}")
                time.sleep(delay)
            finally:
                try:
                    driver.close()
                except Exception as e:
                    print(f"❌ Neo4j connection closed. Error: {e}")
                    pass
        self.stop()
        raise RuntimeError("❌ Neo4j did not become ready in time.")

    def count_nodes(self) -> int | None:
        print("🔍 Checking node count...")
        if self._started:
            driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
            try:
                with driver.session(database=self._db_name) as session:
                    count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
                    print(f"📊 Node count in '{self._db_name}': {count}")
                    return count
            finally:
                driver.close()
        else:
            print("❌ Neo4j did not become ready in time.")
            return None
