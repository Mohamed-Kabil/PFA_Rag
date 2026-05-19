import sys
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

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

print("\nTesting Neo4j Connection...")
try:
    manager = Neo4jManager()
    print("✅ Neo4j Connection Successful")
    manager.close()
except Exception as e:
    print(f"❌ Neo4j Connection failed: {e}")

print("\nTesting Agent Initialization...")
try:
    agent = RoutingAgent("data")
    print("✅ Agent initialized")
except Exception as e:
    print(f"❌ Agent initialization failed: {e}")
    traceback.print_exc()

print("\nTesting Generator Initialization...")
try:
    generator = LocalGenerator()
    print("✅ Generator initialized")
except Exception as e:
    print(f"❌ Generator initialization failed: {e}")
    # traceback.print_exc()

print("\nSummary complete.")
