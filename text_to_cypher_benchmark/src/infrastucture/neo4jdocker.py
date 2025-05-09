from pathlib import Path
import docker
import time
from neo4j import GraphDatabase
import os
from sys import platform
from docker.types import Mount

from text_to_cypher_benchmark.src.configuration import ROOT_DIR

# These constants remain as before
DUMP_PATH = "/absolute/path/to/fincen-50.dump"  # change this as needed
DUMP_NAME = os.path.basename(DUMP_PATH)
DB_NAME = os.path.splitext(DUMP_NAME)[0]
PASSWORD = "neo4j_test_password"


class Neo4jDocker(object):
    _PASSWORD = "neo4j_test_password"
    _USER = "neo4j"
    _DEFAULT = "neo4j"

    def __init__(self, database_name, dump_base=os.path.join(ROOT_DIR, "datasets", "data")):
        self.dump_base = dump_base  # This is used for backup mount (read-only)
        if platform == "darwin":
            colima_socket = os.path.expanduser("~/.colima/default/docker.sock")
            self._client = docker.DockerClient(base_url=f'unix://{colima_socket}')
        else:
            self._client = docker.from_env()
        self._container = None
        self._dump_base = dump_base
        self._database_name = database_name

    def get_username(self):
        return self._USER

    def get_password(self):
        return self._PASSWORD

    def start(self):
        print("Starting neo4j..")
        print(f"Backups path: {self._dump_base}")

        self._container = self._client.containers.run(
            image="neo4j:5.19",
            name="neo4j-benchmark",
            mem_limit="10g",
            command=["bash", "-c", "sleep infinity"],
            environment={
                "NEO4J_AUTH": f"{self._USER}/{self._PASSWORD}",
                # "NEO4J_dbms_default__database": self._database_name,
                "NEO4J_dbms_allow__upgrade": "true"

            },
            ports={"7474/tcp": 7474,
                   "7687/tcp": 7687},
            # Use a host mount for backups (read-only) and a Docker volume for /data.
            mounts=[
                Mount(target="/backups", source=self._dump_base, type="bind", read_only=True),
            ],
            detach=True
        )
        print("Waiting for container to initialize...")
        # Optionally, you may want to add more robust health-check logic here.
        for _ in range(10):
            print(f"Container status: {self._container.status}")
            if self._container.status == "created":
                print("Container is CREATED!")
                wait = 10
                Neo4jDocker._wait(wait)
                return
            else:
                print("Waiting for container to become ready...")
                time.sleep(1)
        self.stop()

    def load(self):
        # The neo4j-admin command expects a directory for --from-path.
        # In this case, we assume that your backup directory (self._dump_base) contains the dump file.
        cmd = (
            f"bin/neo4j-admin database load --verbose --from-path=/backups/  {self._database_name}"
        )
        exec_log = self._container.exec_run(cmd, user="neo4j", demux=True)
        stdout, stderr = exec_log.output
        print("Restore output:\n", (stdout or b"").decode(), (stderr or b"").decode())
        exec_log = self._container.exec_run("bin/neo4j start", user="neo4j" , demux=True)
        stdout, stderr = exec_log.output
        print("Start output:\n", (stdout or b"").decode(), (stderr or b"").decode())


    def stop(self):
        print("Stopping container...")
        try:
            self._container.stop()
            self._container.remove()
            print("Container stopped and removed.")
        except Exception as e:
            print(f"Error stopping container: {e}")
        finally:
            # If the container is already removed, this may raise an exception.
            try:
                self._container.remove()
            except Exception:
                pass

    def get_driver(self, dataset_name):
        uri = "bolt://localhost:7687"

        try:
            driver = GraphDatabase.driver(uri, auth=(self.get_username(), self.get_password()))
            with driver.session(database=dataset_name) as session:
                result = session.run("MATCH (n) RETURN count(n) AS count")
                count = result.single()["count"]
                print(f"✅ Node count in {dataset_name}: {count}")
            driver.close()
        except Exception as e:
            print(f"Error getting driver: {e}")

    @staticmethod
    def _wait(timeout):
        for idx in range(timeout):
            print(f"Waiting for {timeout - idx} sec...")
            time.sleep(1)
