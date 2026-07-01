/**
 * visvalingamWhyatt.js
 *
 * Optimized Visvalingam-Whyatt simplification.
 *
 * Designed for large geometries like:
 * - city boundaries
 * - state boundaries
 * - administrative polygons
 *
 * Uses a priority queue approach to avoid
 * recalculating all triangle areas repeatedly.
 */

import { triangleArea } from "./geometry";

/**
 * Simple Min Heap implementation.
 *
 * The smallest area element is always
 * available at the top.
 */
class MinHeap {
  constructor() {
    this.items = [];
  }

  push(item) {
    this.items.push(item);

    this.bubbleUp();
  }

  pop() {
    if (this.items.length === 1) {
      return this.items.pop();
    }

    const result = this.items[0];

    this.items[0] = this.items.pop();

    this.bubbleDown();

    return result;
  }

  bubbleUp() {
    let index = this.items.length - 1;

    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);

      if (this.items[parent].area <= this.items[index].area) {
        break;
      }

      [this.items[parent], this.items[index]] = [
        this.items[index],
        this.items[parent],
      ];

      index = parent;
    }
  }

  bubbleDown() {
    let index = 0;

    while (true) {
      let smallest = index;

      const left = index * 2 + 1;

      const right = index * 2 + 2;

      if (
        left < this.items.length &&
        this.items[left].area < this.items[smallest].area
      ) {
        smallest = left;
      }

      if (
        right < this.items.length &&
        this.items[right].area < this.items[smallest].area
      ) {
        smallest = right;
      }

      if (smallest === index) {
        break;
      }

      [this.items[index], this.items[smallest]] = [
        this.items[smallest],
        this.items[index],
      ];

      index = smallest;
    }
  }

  get size() {
    return this.items.length;
  }
}

/**
 * Creates a triangle area value for one vertex.
 *
 * @param {Array} points
 * @param {number} index
 */
function calculateEffectiveArea(points, index) {
  const previous = points[index - 1];

  const current = points[index];

  const next = points[index + 1];

  return triangleArea(previous, current, next);
}

/**
 * Optimized Visvalingam-Whyatt algorithm.
 *
 * @param {Array<number[]>} points
 * @param {number} minArea
 *
 * @returns {Array<number[]>}
 */
export function simplifyVisvalingam(points, minArea = 0.000001) {
  if (points.length <= 2) {
    return points;
  }

  /*
   * Store points with an id.
   *
   * The id allows us to track removed vertices.
   */
  const vertices = points.map((point, index) => ({
    point,

    index,

    removed: false,
  }));

  const heap = new MinHeap();

  /*
   * Calculate initial triangle areas.
   */
  for (let i = 1; i < vertices.length - 1; i++) {
    heap.push({
      index: i,

      area: calculateEffectiveArea(points, i),
    });
  }

  /*
   * Remove the least important points.
   */
  while (heap.size > 0) {
    const smallest = heap.pop();

    const vertex = vertices[smallest.index];

    if (vertex.removed) {
      continue;
    }

    if (smallest.area >= minArea) {
      break;
    }

    /*
     * Remove vertex.
     */
    vertex.removed = true;

    /*
     * Recalculate neighboring vertices.
     */
    const left = smallest.index - 1;

    const right = smallest.index + 1;

    if (left > 0 && !vertices[left].removed) {
      heap.push({
        index: left,

        area: calculateEffectiveArea(points, left),
      });
    }

    if (right < vertices.length - 1 && !vertices[right].removed) {
      heap.push({
        index: right,

        area: calculateEffectiveArea(points, right),
      });
    }
  }

  /*
   * Rebuild final geometry.
   */
  return vertices.filter((v) => !v.removed).map((v) => v.point);
}
