import certifi
import os
from neo4j import GraphDatabase

os.environ['SSL_CERT_FILE'] = certifi.where()

URI = "neo4j+s://fc15b342.databases.neo4j.io"
AUTH = ("neo4j", "your_password")

driver = GraphDatabase.driver(URI, auth=AUTH)

with driver.session() as session:
    print(session.run("RETURN 'Connected' AS msg").single()["msg"])
