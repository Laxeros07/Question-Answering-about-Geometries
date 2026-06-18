#!/bin/bash

echo "Waiting for Neo4j..."

until cypher-shell \
  -a bolt://neo4j:7687 \
  -u neo4j \
  -p password \
  "RETURN 1" > /dev/null 2>&1
do
  sleep 5
done

echo "Neo4j ready. Importing data..."

cypher-shell \
  -a bolt://neo4j:7687 \
  -u neo4j \
  -p password \
  -f /scripts/import.cypher

echo "Import finished."