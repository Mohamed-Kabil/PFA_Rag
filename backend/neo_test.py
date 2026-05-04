import certifi
import os
from neo4j import GraphDatabase

os.environ['SSL_CERT_FILE'] = certifi.where()

URI = "neo4j+s://fc15b342.databases.neo4j.io"
AUTH = ("neo4j", "Ay4vQ4hdOmjgH7x2q2-JwqW27f6LFC_CHgTMGv_0Z1I")

driver = GraphDatabase.driver(URI, auth=AUTH)

with driver.session() as session:
    print(session.run("RETURN 'Connected' AS msg").single()["msg"])
