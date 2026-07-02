/**
 * Processes geometry objects for genralization.
 */

import { processGeometry } from "./geojson";

export function processGeometries(geometries, algorithm, parameter) {
  return geometries.map((item) => {
    return {
      ...item,

      geojson: processGeometry(item.geojson, algorithm, parameter),
    };
  });
}
