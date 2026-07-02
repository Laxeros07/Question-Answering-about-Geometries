/**
 * geojson.js
 *
 * Applies generalization algorithms to GeoJSON geometries.
 *
 * Handles:
 * - Polygon
 * - MultiPolygon
 *
 * Coordinates are projected before processing
 * so algorithms work with meters instead of degrees.
 */

import * as Geometry from "../algorithms/geometry";

import { projectRing, unprojectRing } from "./projection";

/**
 * Processes one polygon ring.
 *
 * Workflow:
 *
 * GeoJSON coordinates
 *        |
 *        v
 * remove closing point
 *        |
 *        v
 * project to meters
 *        |
 *        v
 * algorithm
 *        |
 *        v
 * back to longitude/latitude
 *        |
 *        v
 * close ring
 *
 */
function processRing(ring, algorithm, parameter) {
  /*
   * Remove duplicated first/last point.
   */
  const open = Geometry.openRing(ring);

  /*
   * Convert:
   *
   * [lon,lat]
   *
   * to:
   *
   * [meters,meters]
   */
  const projected = projectRing(open);

  /*
   * Run Douglas / Visvalingam / Chaikin
   *
   * parameter is now in meters
   */
  const processed = algorithm(projected, parameter);

  /*
   * Convert back to GeoJSON coordinates.
   */
  const unprojected = unprojectRing(processed);

  /*
   * GeoJSON polygons must be closed.
   */
  return Geometry.closeRing(unprojected);
}

/**
 * Processes Polygon geometry.
 */
export function processPolygon(polygon, algorithm, parameter) {
  return {
    ...polygon,

    coordinates: polygon.coordinates.map((ring) =>
      processRing(ring, algorithm, parameter),
    ),
  };
}

/**
 * Processes MultiPolygon geometry.
 */
export function processMultiPolygon(multiPolygon, algorithm, parameter) {
  return {
    ...multiPolygon,

    coordinates: multiPolygon.coordinates.map((polygon) =>
      polygon.map((ring) => processRing(ring, algorithm, parameter)),
    ),
  };
}

/**
 * Automatically detects geometry type.
 */
export function processGeometry(geometry, algorithm, parameter) {
  switch (geometry.type) {
    case "Polygon":
      return processPolygon(geometry, algorithm, parameter);

    case "MultiPolygon":
      return processMultiPolygon(geometry, algorithm, parameter);

    default:
      throw new Error(`Unsupported type: ${geometry.type}`);
  }
}
