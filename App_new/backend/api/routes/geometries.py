from fastapi import APIRouter, HTTPException, Query
import pandas as pd
import json

router = APIRouter(prefix="/api/geometries")

# Load at the start
df = pd.read_csv("data/geometries.csv")
df.set_index("ID", inplace=True)

# ---------------------------------------------------
# Multiple geometries by IDs
# ---------------------------------------------------
@router.get("/")
def get_geometries(ids: str = Query(None)):
    """
    Example:
    /api/geometries?ids=C1,C2,C3
    """

    if not ids:
        return {"error": "No ids provided"}

    id_list = ids.split(",")

    result = []

    for geom_id in id_list:
        if geom_id in df.index:
            result.append({
                "id": geom_id,
                "geojson": json.loads(df.loc[geom_id]["Geometry"])
            })

    return {"geometries": result}