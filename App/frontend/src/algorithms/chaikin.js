/**
 * Chaikin corner cutting algorithm.
 *
 * This algorithm smooths polygon boundaries by
 * replacing corners with new points.
 *
 * Unlike Douglas-Peucker or Visvalingam-Whyatt,
 * Chaikin does not remove points.
 * It creates additional vertices.
 *
 * Input:
 *
 * [
 *   [x, y],
 *   [x, y],
 *   ...
 * ]
 *
 * Output:
 *
 * [
 *   [x, y],
 *   [x, y],
 *   ...
 * ]
 */

import { isClosed, closeRing, openRing } from "./geometry";

/**
 * Creates a new point between two points.
 *
 * ratio 0.25 creates a point one quarter
 * along the line.
 *
 * @param {number[]} p1
 * @param {number[]} p2
 * @param {number} ratio
 *
 * @returns {number[]}
 */
function interpolate(p1, p2, ratio) {
  return [p1[0] + (p2[0] - p1[0]) * ratio, p1[1] + (p2[1] - p1[1]) * ratio];
}

/**
 * Performs one Chaikin iteration.
 *
 * One iteration replaces every edge
 * with two new points.
 *
 * @param {Array<number[]>} points
 *
 * @returns {Array<number[]>}
 */
function chaikinIteration(points) {
  const result = [];

  for (let i = 0; i < points.length - 1; i++) {
    const current = points[i];

    const next = points[i + 1];

    /*
     * First new point:
     * 25% from current towards next
     */
    const q = interpolate(current, next, 0.25);

    /*
     * Second new point:
     * 75% from current towards next
     */
    const r = interpolate(current, next, 0.75);

    result.push(q);

    result.push(r);
  }

  return result;
}

/**
 * Applies Chaikin smoothing.
 *
 * @param {Array<number[]>} points
 * @param {number} iterations
 *
 * @returns {Array<number[]>}
 */
export function chaikin(points, iterations = 2) {
  if (points.length < 3) {
    return points;
  }

  /*
   * Check if the input is a polygon ring.
   */
  const wasClosed = isClosed(points);

  /*
   * Work on an open ring.
   */
  let result = openRing(points);

  /*
   * Apply smoothing multiple times.
   */
  for (let i = 0; i < iterations; i++) {
    result = chaikinIteration(result);
  }

  /*
   * Restore polygon closure.
   */
  if (wasClosed) {
    result = closeRing(result);
  }

  return result;
}
