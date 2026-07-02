/**
 * geometry.js
 *
 * Shared geometric helper functions used by the generalization algorithms.
 *
 * A point is represented as:
 * [x, y]
 *
 * Example:
 * const point = [7.1234, 51.4567];
 */

/**
 * Calculates the Euclidean distance between two points.
 *
 * @param {number[]} p1 - First point [x, y]
 * @param {number[]} p2 - Second point [x, y]
 * @returns {number} Distance between the two points
 */
export function distance(p1, p2) {
  const dx = p2[0] - p1[0];
  const dy = p2[1] - p1[1];

  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Calculates the perpendicular distance from a point
 * to the line segment defined by two points.
 *
 * This function is required by the Douglas-Peucker algorithm.
 *
 * @param {number[]} point - Point to test [x, y]
 * @param {number[]} start - Start point of the line segment
 * @param {number[]} end - End point of the line segment
 * @returns {number} Perpendicular distance
 */
export function perpendicularDistance(point, start, end) {
  const x = point[0];
  const y = point[1];

  const x1 = start[0];
  const y1 = start[1];

  const x2 = end[0];
  const y2 = end[1];

  // Handle the special case where start and end are identical.
  if (x1 === x2 && y1 === y2) {
    return distance(point, start);
  }

  const numerator = Math.abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1);

  const denominator = Math.sqrt(Math.pow(y2 - y1, 2) + Math.pow(x2 - x1, 2));

  return numerator / denominator;
}

/**
 * Calculates the area of a triangle using the shoelace formula.
 *
 * This function is used by the Visvalingam-Whyatt algorithm
 * to determine the importance of a vertex.
 *
 * @param {number[]} a - First vertex
 * @param {number[]} b - Second vertex
 * @param {number[]} c - Third vertex
 * @returns {number} Triangle area
 */
export function triangleArea(a, b, c) {
  return Math.abs(
    (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1])) / 2,
  );
}

/**
 * Checks whether a polygon ring is closed.
 *
 * A GeoJSON polygon ring is closed if its first and last
 * coordinate are identical.
 *
 * @param {Array<number[]>} points
 * @returns {boolean}
 */
export function isClosed(points) {
  if (points.length < 2) {
    return false;
  }

  const first = points[0];
  const last = points[points.length - 1];

  return first[0] === last[0] && first[1] === last[1];
}

/**
 * Ensures that a polygon ring is closed.
 *
 * If the first and last point differ,
 * the first point is appended to the end.
 *
 * @param {Array<number[]>} points
 * @returns {Array<number[]>}
 */
export function closeRing(points) {
  if (isClosed(points)) {
    return [...points];
  }

  return [...points, points[0]];
}

/**
 * Removes the duplicated closing point from a polygon ring.
 *
 * Some algorithms are easier to implement on an open ring.
 *
 * @param {Array<number[]>} points
 * @returns {Array<number[]>}
 */
export function openRing(points) {
  if (!isClosed(points)) {
    return [...points];
  }

  return points.slice(0, -1);
}
