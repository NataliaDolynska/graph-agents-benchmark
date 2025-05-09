from text_to_cypher_benchmark.src.configuration import ROOT_DIR
from text_to_cypher_benchmark.src.infrastucture.neo4jdocker import Neo4jDocker

print(f"AAAA: {ROOT_DIR}")
n4j  =  Neo4jDocker("recommendations-50")
print("SSDAD")

# 
n4j.start()
print("FFFFF")
# 
n4j.load()
print("222222")
n4j.get_driver("recommendations-50")
# 
print("BBBBB")
n4j.stop()
print("EEEE")
