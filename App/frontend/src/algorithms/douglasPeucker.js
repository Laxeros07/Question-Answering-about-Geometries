/**
 * douglasPeucker.js
 *
 * Douglas-Peucker line simplification algorithm.
 *
 * The algorithm reduces the number of vertices while
 * preserving the overall shape of the geometry.
 *
 * Input format:
 * [
 *   [x, y],
 *   [x, y],
 *   ...
 * ]
 *
 * Output format:
 * [
 *   [x, y],
 *   [x, y],
 *   ...
 * ]
 */

import { perpendicularDistance } from "./geometry";

/**
 * Recursive Douglas-Peucker implementation.
 *
 * @param {Array<number[]>} points
 * @param {number} tolerance
 *
 * @returns {Array<number[]>}
 */
function simplify(points, tolerance) {
  // A line with two points cannot be simplified.
  if (points.length <= 2) {
    return points;
  }

  const firstPoint = points[0];
  const lastPoint = points[points.length - 1];

  let maxDistance = 0;
  let maxIndex = 0;

  /*
   * Find the point with the maximum distance
   * from the line between first and last point.
   */
  for (let i = 1; i < points.length - 1; i++) {
    const distance = perpendicularDistance(points[i], firstPoint, lastPoint);

    if (distance > maxDistance) {
      maxDistance = distance;
      maxIndex = i;
    }
  }

  /*
   * If the furthest point is outside the tolerance,
   * keep it and simplify both resulting sections.
   */
  if (maxDistance > tolerance) {
    const left = points.slice(0, maxIndex + 1);

    const right = points.slice(maxIndex);

    const simplifiedLeft = simplify(left, tolerance);

    const simplifiedRight = simplify(right, tolerance);

    /*
     * The last point of the left side is the same
     * as the first point of the right side.
     *
     * Remove the duplicate point.
     */
    return [...simplifiedLeft.slice(0, -1), ...simplifiedRight];
  }

  /*
   * If no point exceeds the tolerance,
   * only keep start and end point.
   */
  return [firstPoint, lastPoint];
}

/**
 * Public Douglas-Peucker function.
 *
 * This is the function that should be imported
 * by the application.
 *
 * @param {Array<number[]>} points
 * @param {number} tolerance
 *
 * @returns {Array<number[]>}
 */
export function simplifyDouglasPeucker(points, tolerance = 0.0001) {
  /*
   * Run the algorithm.
   */
  return simplify(points, tolerance);
}
