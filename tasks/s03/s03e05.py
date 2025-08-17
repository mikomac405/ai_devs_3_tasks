from neo4j import GraphDatabase
import json
import os

URI = "neo4j://localhost:7687"

task_files = os.path.join("data", "s03e05")

with open(os.path.join(task_files, "users.json"), encoding='utf-8') as f:
    users = json.load(f)["reply"]

with open(os.path.join(task_files, "connections.json")) as f:
    connections = json.load(f)["reply"]


def create_user(driver, userid, username):
    driver.execute_query("""
    CREATE (p:Person {userid: $userid, username: $username})    
    """,
    userid=userid, username=username, database_="neo4j"
    )

def create_connection_between_users(driver, user1_id, user2_id):
    driver.execute_query("""
    MATCH (a:Person), (b:Person)
    WHERE a.userid = $user1_id AND b.userid = $user2_id
    CREATE (a)-[:KNOWS]->(b)                              
    """,
    user1_id=user1_id, user2_id=user2_id, database_="neo4j"
    )

with GraphDatabase.driver(URI) as driver:
    driver.verify_connectivity()
    for user in users:
        create_user(driver, user['id'], user['username'])
    for connection in connections:
        create_connection_between_users(driver, connection["user1_id"], connection["user2_id"])