/**
 * projection.js
 *
 * Coordinate transformation helpers.
 *
 * GeoJSON uses EPSG:4326:
 * longitude / latitude
 *
 * Geometry algorithms work better with
 * metric coordinates: meters
 *
 * This file handles:
 * EPSG:4326 <-> EPSG:3857
 */

import proj4 from "proj4";

/**
 * Source coordinate system.
 * Standard GeoJSON coordinates.
 */
const WGS84 = "EPSG:4326";

/**
 * Web Mercator projection.
 *
 * Uses meters.
 *
 * Good enough for visualization
 * and map generalization.
 */
const METERS = "EPSG:3857";

/**
 * Projects one coordinate.
 *
 * Input:
 * [longitude, latitude]
 *
 * Output:
 * [x meters, y meters]
 *
 * @param {number[]} coordinate
 *
 * @returns {number[]}
 */
export function projectCoordinate(coordinate) {
  return proj4(WGS84, METERS, coordinate);
}

/**
 * Converts one coordinate back.
 *
 * Input:
 * [x meters, y meters]
 *
 * Output:
 * [longitude, latitude]
 *
 * @param {number[]} coordinate
 *
 * @returns {number[]}
 */
export function unprojectCoordinate(coordinate) {
  return proj4(METERS, WGS84, coordinate);
}

/**
 * Projects a complete ring.
 *
 * @param {Array<number[]>} ring
 *
 * @returns {Array<number[]>}
 */
export function projectRing(ring) {
  return ring.map(projectCoordinate);
}

/**
 * Converts a complete ring back.
 *
 * @param {Array<number[]>} ring
 *
 * @returns {Array<number[]>}
 */
export function unprojectRing(ring) {
  return ring.map(unprojectCoordinate);
}

/**
 * Projects a Polygon coordinate array.
 *
 * Polygon:
 * [
 *   outerRing,
 *   innerRing
 * ]
 *
 */
export function projectPolygon(coordinates) {
  return coordinates.map((ring) => projectRing(ring));
}

/**
 * Converts Polygon coordinates back.
 */
export function unprojectPolygon(coordinates) {
  return coordinates.map((ring) => unprojectRing(ring));
}
