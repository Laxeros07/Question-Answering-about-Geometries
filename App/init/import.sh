#!/bin/bash

NEO4J_URI=${NEO4J_URI:-bolt://neo4j:7687}
NEO4J_USER=${NEO4J_USER:-neo4j}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-password}

echo "Waiting for Neo4j..."

until cypher-shell \
  -a ${NEO4J_URI} \
  -u ${NEO4J_USER} \
  -p ${NEO4J_PASSWORD} \
  "RETURN 1" > /dev/null 2>&1
do
  sleep 5
done

echo "Neo4j ready. Importing data..."

cypher-shell \
  -a ${NEO4J_URI} \
  -u ${NEO4J_USER} \
  -p ${NEO4J_PASSWORD} \
  -f /scripts/import.cypher

echo "Import finished."