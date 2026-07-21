# Graph Data Processing

This folder contains the Python pipeline used to prepare the data for the project’s knowledge graph and backend. The scripts read shapefiles, derive spatial relationships, and generate CSV files that are later imported into Neo4j or used by the application.

## Folder contents

- [Data Management](Data%20Management) – main processing scripts and shapefile source data
- [Data Management/Geometries/Shapes](Data%20Management/Geometries/Shapes) – input shapefiles for municipalities, administrative communities, districts, administrative districts, federal states and states
- [start.bat](start.bat) – Is needed for starting the local Neo4J database. Is not needed for the calculation of the csv files.

## Main workflow

The processing pipeline is orchestrated by [Data Management/main.py](Data%20Management/main.py). It runs the following steps:

1. Load the required spatial layers from the shapefiles.
2. Process the layers to assign IDs, centroids, and parent relationships.
3. Generate relationship files for:
   - hierarchy information (`within`)
   - neighboring geometries (`touches`)
   - ~~spatial distance and direction relations (`relates`)~~ (this operation was deleted, but the code stayed)
4. Write the resulting CSV files into the application folders.

## Python scripts

### [Data Management/main.py](Data%20Management/main.py)
Entry point for the full pipeline. It calls the loader, processor, and writer modules and can be configured to generate all or only selected CSV files.

Supported generation options:
- `all`
- `layers`
- `within`
- `touches`
- ~~`relates`~~

### [Data Management/loader.py](Data%20Management/loader.py)
Loads the shapefiles from the geometry data folder and prepares the base geospatial layers.

### [Data Management/processor.py](Data%20Management/processor.py)
Contains the main data-processing logic:
- creates IDs for each feature
- derives centroids
- builds parent-child relationships between administrative levels
- computes `within`, `touches`, and ~~`relates`~~ relations

### [Data Management/writer.py](Data%20Management/writer.py)
Writes the generated data to CSV files. The output is stored in:
- [App/neo4j_data](../App/neo4j_data) for Neo4j import
- [App/backend/data](../App/backend/data) for backend usage

## Generated CSV files

The pipeline creates files such as:

- `cities.csv`
- `administrativeCommunities.csv`
- `districts.csv`
- `administrativeDistricts.csv`
- `federalStates.csv`
- `states.csv`
- `geometryTypes.csv`
- `hasFootprint.csv`
- `within.csv`
- `touches.csv`
- ~~`relates.csv`~~
- `geometries.csv`

## How to run

From the repository root, run:

```bash
python "Graph/Data Management/main.py"
```

This will generate the default set of CSV files.

## Requirements

The scripts depend on Python packages such as:

- `geopandas`
- `numpy`
- `pandas`
