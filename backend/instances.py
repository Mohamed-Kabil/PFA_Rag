from backend.agent import RoutingAgent
from backend.generation import LocalGenerator
from backend.neo4j_manager import Neo4jManager
from backend import config

agent = RoutingAgent(config.DATA_DIR)
generator = LocalGenerator()
neo4j_manager = Neo4jManager()
