:param {
  // Define the file path root and the individual file names required for loading.
  // https://neo4j.com/docs/operations-manual/current/configuration/file-locations/
  file_path_root: 'file:///', // Change this to the folder your script can access the files at.
  file_0: 'geometryTypes.csv',
  file_1: 'cities.csv',
  file_2: 'districts.csv',
  file_3: 'administrativeDistricts.csv',
  file_4: 'federalStates.csv',
  file_5: 'administrativeCommunities.csv',
  file_6: 'hasFootprint.csv',
  file_7: 'within.csv',
  file_8: 'touches.csv'
};

// CONSTRAINT creation
// -------------------
//
// Create node uniqueness constraints, ensuring no duplicates for the given node label and ID property exist in the database. This also ensures no duplicates are introduced in future.
//
// NOTE: The following constraint creation syntax is valid for database version 4.4.0 and above.
CREATE CONSTRAINT `ID_Geometry_uniq` IF NOT EXISTS
FOR (n: `Geometry`)
REQUIRE (n.`ID`) IS UNIQUE;
CREATE CONSTRAINT `ID_City_uniq` IF NOT EXISTS
FOR (n: `City`)
REQUIRE (n.`ID`) IS UNIQUE;
CREATE CONSTRAINT `ID_District_uniq` IF NOT EXISTS
FOR (n: `District`)
REQUIRE (n.`ID`) IS UNIQUE;
CREATE CONSTRAINT `ID_AdministrativeDistrict_uniq` IF NOT EXISTS
FOR (n: `AdministrativeDistrict`)
REQUIRE (n.`ID`) IS UNIQUE;
CREATE CONSTRAINT `ID_FederalState_uniq` IF NOT EXISTS
FOR (n: `FederalState`)
REQUIRE (n.`ID`) IS UNIQUE;
CREATE CONSTRAINT `ID_AdministrativeCommunity_uniq` IF NOT EXISTS
FOR (n: `AdministrativeCommunity`)
REQUIRE (n.`ID`) IS UNIQUE;

:param {
  idsToSkip: []
};

// NODE load
// ---------
//
// Load nodes in batches, one node label at a time. Nodes will be created using a MERGE statement to ensure a node with the same label and ID property remains unique. Pre-existing nodes found by a MERGE statement will have their other properties set to the latest values encountered in a load file.
//
// NOTE: Any nodes with IDs in the 'idsToSkip' list parameter will not be loaded.
LOAD CSV WITH HEADERS FROM ($file_path_root + $file_0) AS row
WITH row
WHERE NOT row.`ID` IN $idsToSkip AND NOT row.`ID` IS NULL
CALL {
  WITH row
  MERGE (n: `Geometry` { `ID`: row.`ID` })
  SET n.`ID` = row.`ID`
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_1) AS row
WITH row
WHERE NOT row.`ID` IN $idsToSkip AND NOT row.`ID` IS NULL
CALL {
  WITH row
  MERGE (n: `City` { `ID`: row.`ID` })
  SET n.`ID` = row.`ID`
  SET n.`Name` = row.`Name`
  SET n.`Centroid` = row.`Centroid`
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_2) AS row
WITH row
WHERE NOT row.`ID` IN $idsToSkip AND NOT row.`ID` IS NULL
CALL {
  WITH row
  MERGE (n: `District` { `ID`: row.`ID` })
  SET n.`ID` = row.`ID`
  SET n.`Name` = row.`Name`
  SET n.`Centroid` = row.`Centroid`
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_3) AS row
WITH row
WHERE NOT row.`ID` IN $idsToSkip AND NOT row.`ID` IS NULL
CALL {
  WITH row
  MERGE (n: `AdministrativeDistrict` { `ID`: row.`ID` })
  SET n.`ID` = row.`ID`
  SET n.`Name` = row.`Name`
  SET n.`Centroid` = row.`Centroid`
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_4) AS row
WITH row
WHERE NOT row.`ID` IN $idsToSkip AND NOT row.`ID` IS NULL
CALL {
  WITH row
  MERGE (n: `FederalState` { `ID`: row.`ID` })
  SET n.`ID` = row.`ID`
  SET n.`Name` = row.`Name`
  SET n.`Centroid` = row.`Centroid`
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_5) AS row
WITH row
WHERE NOT row.`ID` IN $idsToSkip AND NOT row.`ID` IS NULL
CALL {
  WITH row
  MERGE (n: `AdministrativeCommunity` { `ID`: row.`ID` })
  SET n.`ID` = row.`ID`
  SET n.`Name` = row.`Name`
  SET n.`Centroid` = row.`Centroid`
} IN TRANSACTIONS OF 10000 ROWS;


// RELATIONSHIP load
// -----------------
//
// Load relationships in batches, one relationship type at a time. Relationships are created using a MERGE statement, meaning only one relationship of a given type will ever be created between a pair of nodes.
LOAD CSV WITH HEADERS FROM ($file_path_root + $file_6) AS row
WITH row 
CALL {
  WITH row
  MATCH (source: `City` { `ID`: row.`Start_Point` })
  MATCH (target: `Geometry` { `ID`: row.`End_Point` })
  MERGE (source)-[r: `hasFootprint`]->(target)
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_6) AS row
WITH row 
CALL {
  WITH row
  MATCH (source: `District` { `ID`: row.`Start_Point` })
  MATCH (target: `Geometry` { `ID`: row.`End_Point` })
  MERGE (source)-[r: `hasFootprint`]->(target)
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_6) AS row
WITH row 
CALL {
  WITH row
  MATCH (source: `AdministrativeDistrict` { `ID`: row.`Start_Point` })
  MATCH (target: `Geometry` { `ID`: row.`End_Point` })
  MERGE (source)-[r: `hasFootprint`]->(target)
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_6) AS row
WITH row 
CALL {
  WITH row
  MATCH (source: `FederalState` { `ID`: row.`Start_Point` })
  MATCH (target: `Geometry` { `ID`: row.`End_Point` })
  MERGE (source)-[r: `hasFootprint`]->(target)
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_7) AS row
WITH row 
CALL {
  WITH row
  MATCH (source: `Geometry` { `ID`: row.`Start_Point` })
  MATCH (target: `Geometry` { `ID`: row.`End_Point` })
  MERGE (source)-[r: `within`]->(target)
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_8) AS row
WITH row 
CALL {
  WITH row
  MATCH (source: `Geometry` { `ID`: row.`Start_Point` })
  MATCH (target: `Geometry` { `ID`: row.`End_Point` })
  MERGE (source)-[r: `touches`]->(target)
  SET r.`Rel_Position` = row.`Rel_Position`
} IN TRANSACTIONS OF 10000 ROWS;

LOAD CSV WITH HEADERS FROM ($file_path_root + $file_6) AS row
WITH row 
CALL {
  WITH row
  MATCH (source: `AdministrativeCommunity` { `ID`: row.`Start_Point` })
  MATCH (target: `Geometry` { `ID`: row.`End_Point` })
  MERGE (source)-[r: `hasFootprint`]->(target)
} IN TRANSACTIONS OF 10000 ROWS;
