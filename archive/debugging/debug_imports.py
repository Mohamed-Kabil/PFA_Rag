import sys
import os
import traceback

print("Checking imports...")
try:
    from backend.agent import RoutingAgent
    print("Agent imported")
    from backend.generation import LocalGenerator
    print("Generator imported")
    from backend.neo4j_manager import Neo4jManager
    print("Neo4jManager imported")
except Exception as e:
    print(f"Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Initializing Agent...")
try:
    agent = RoutingAgent("data")
    print("Agent initialized")
except Exception as e:
    print(f"Agent initialization failed: {e}")
    traceback.print_exc()

print("Initializing Generator...")
try:
    generator = LocalGenerator()
    print("Generator initialized")
except Exception as e:
    print(f"Generator initialization failed: {e}")
    traceback.print_exc()

print("Success!")
