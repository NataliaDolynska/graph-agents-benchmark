import docker
import time
from neo4j import GraphDatabase
import os

DUMP_PATH = "/absolute/path/to/fincen-50.dump"  # change this
DUMP_NAME = os.path.basename(DUMP_PATH)
DB_NAME = os.path.splitext(DUMP_NAME)[0]
PASSWORD = "neo4j_test_password"

# Set DOCKER_HOST to Colima's socket
colima_socket = os.path.expanduser("~/.colima/default/docker.sock")
client = docker.DockerClient(base_url=f'unix://{colima_socket}')

print(f"Starting Neo4j container with DB: {DB_NAME}")

container = client.containers.run(
    image="neo4j:5.19",
    name=f"neo4j-{DB_NAME}",
    environment={
        "NEO4J_AUTH": f"neo4j/{PASSWORD}",
        "NEO4J_dbms_default__database": DB_NAME
    },
    ports={"7474/tcp": 7474, "7687/tcp": 7687},
    volumes={
        DUMP_PATH: {"bind": f"/backups/{DUMP_NAME}", "mode": "ro"}
    },
    detach=True
)

# 2. Wait for Neo4j admin tool to be available
print("Waiting for container to initialize...")
for _ in range(10):
    print(f"Status of container initialization: {container.status}")
    time.sleep(1)


time.sleep(10)

# 3. Run the restore command
print("Restoring dump...")
cmd = (
    f"bin/neo4j-admin database load  --from-path=/backups {DB_NAME} --overwrite-destination=true"
)

exec_log = container.exec_run(cmd, user="neo4j", demux=True)
stdout, stderr = exec_log.output
print("Restore output:\n", (stdout or b"").decode(), (stderr or b"").decode())

# 4. Wait for the database to be ready (simplified with sleep)
print("Waiting for Neo4j to finish booting...")
time.sleep(15)

# 5. Run a test query
uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", PASSWORD))


print(f"DATBASE: {DB_NAME}")
with driver.session(database=DB_NAME) as session:
    result = session.run("MATCH (n) RETURN count(n) AS count")
    count = result.single()["count"]
    print(f"✅ Node count in {DB_NAME}: {count}")

driver.close()

# 6. Cleanup
print("Stopping and removing container...")
container.stop()
container.remove()
print("✅ Done.")
