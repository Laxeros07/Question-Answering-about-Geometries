import L from "leaflet";
import { API_BASE_URL } from "./constants";

/**
 * Returns the color for a given geometry type.
 */
export function getColor(d) {
  return d === "City" || d === "C"
    ? "#3A27D0"
    : d === "Administrative community" || d === "V"
      ? "#00aeff"
      : d === "District" || d === "D"
        ? "#f04b23"
        : d === "Administrative district" || d === "A"
          ? "#ffcc00"
          : d === "Federal state" || d === "F"
            ? "#469F4E"
            : "#fff";
}

// Mapping ID prefixes to readable level names
export function getLevelName(typeCode) {
  switch (typeCode) {
    case "C":
      return "City";
    case "V":
      return "AdministrativeCommunity";
    case "D":
      return "District";
    case "A":
      return "AdministrativeDistrict";
    case "F":
      return "FederalState";
    default:
      return "Unknown";
  }
}

/**
 * Loads the geometries for the given search IDs and adds them to the map.
 */
export async function loadGeometries(searchIDs, map) {
  const { cityLayer, acLayer, districtLayer, adLayer, fsLayer } = map.layers;
  const data = await fetchGeometries(searchIDs);

  data.forEach((item) => {
    const color = getColor(item.type);

    // feature properties
    const featureProperties = {
      name: item.name,
      level: getLevelName(item.type),
    };

    // wrap feature to Geojson
    const geojsonFeature = {
      type: "Feature",
      properties: featureProperties,
      geometry: item.geometry?.geometry || item.geometry,
    };

    const layer = L.geoJSON(geojsonFeature, {
      style: {
        color,
        fillColor: color,
        weight: 3,
        opacity: 0.65,
        fillOpacity: 0.35,
      },
      onEachFeature: (feature, l) => {
        // Pop-up with name + layer
        l.bindPopup(
          `<strong>${item.name}</strong><br>${getLevelName(item.type)}`,
        );
      },
      pane: item.type,
    });

    switch (item.type) {
      case "C":
        cityLayer.addLayer(layer);
        break;
      case "V":
        acLayer.addLayer(layer);
        break;
      case "D":
        districtLayer.addLayer(layer);
        break;
      case "A":
        adLayer.addLayer(layer);
        break;
      case "F":
        fsLayer.addLayer(layer);
        break;
      default:
        break;
    }
  });

  const group = L.featureGroup([
    cityLayer,
    acLayer,
    districtLayer,
    adLayer,
    fsLayer,
  ]);
  map.flyToBounds(group.getBounds());
}

/**
 * Removes all geometries from the map
 */
export function clearGeometries(mapRef) {
  if (!mapRef.current?.layers) return;

  const { cityLayer, acLayer, districtLayer, adLayer, fsLayer } =
    mapRef.current.layers;
  cityLayer.clearLayers();
  acLayer.clearLayers();
  districtLayer.clearLayers();
  adLayer.clearLayers();
  fsLayer.clearLayers();
}

/**
 * Fetches geometry data for the given search IDs.
 */
export async function fetchGeometries(searchIDs) {
  let ids = [];
  searchIDs.forEach((item) => {
    if (item.name !== null) {
      ids.push(item.id);
    }
  });
  const res = await fetch(
    `${API_BASE_URL}/api/geometries?ids=` + ids.join(","),
  );
  const rows = await res.json();

  return searchIDs
    .map((item) => {
      const result = rows.geometries.find((row) => row.id === item.id);

      if (!result) return null;
      if (item.name == null) return null;

      return {
        id: item.id,
        name: item.name,
        type: item.id[0],
        geometry: result.geojson,
      };
    })
    .filter(Boolean);
}

/**
 * Exports a Leaflet layer or all map layers as a GeoJSON file.
 */
export function exportLayerToGeoJSON(
  layerOrKey,
  map,
  filename = "map-export.geojson",
  geojsonOverride = null,
) {
  let layer;

  if (typeof layerOrKey === "string") {
    layer = map.layers[layerOrKey];
  } else {
    layer = layerOrKey;
  }

  if (!layer || layer.getLayers().length === 0) {
    alert("Keine Daten in diesem Layer zum Exportieren vorhanden.");
    return;
  }

  try {
    const geojsonData = geojsonOverride ?? layer.toGeoJSON();

    const jsonString = JSON.stringify(geojsonData, null, 2);

    const blob = new Blob([jsonString], { type: "application/json" });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Export failed:", error);

    alert("An error occurred during export.");
  }
}

// Get GErmany Borders
export async function loadGermanyBorder(map) {
  const res = await fetch(`${API_BASE_URL}/api/geometries?ids=S1`);
  const data = await res.json();

  const germany = data.geometries[0];

  if (!germany) {
    console.error("Germany geometry not found");
    return;
  }

  const layer = L.geoJSON(germany.geojson, {
    style: {
      color: "#7a7a7a",
      weight: 3,
      fillOpacity: 0,
    },
    pane: "Germany",
  });

  map.layers.germanyLayer.addLayer(layer);
}
