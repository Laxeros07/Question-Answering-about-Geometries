/**
 * index.js
 *
 * Central export file for all geometry generalization algorithms.
 * This file acts as the public API of the algorithms folder.
 *
 * Instead of importing every algorithm separately:
 * import { simplifyDouglasPeucker }
 * from "./douglasPeucker";
 *
 * the application can simply use:
 * import { algorithms }
 * from "./algorithms";
 */

import { simplifyDouglasPeucker } from "./douglasPeucker";
import { simplifyVisvalingam } from "./visvalingamWhyatt";
import { chaikin } from "./chaikin";

/**
 * Collection of available algorithms.
 * The key names are used by the frontend.
 *
 * Example:
 * algorithms["douglas"]
 *
 * executes:
 * simplifyDouglasPeucker()
 */
export const algorithms = {
  douglas: simplifyDouglasPeucker,
  visvalingam: simplifyVisvalingam,
  chaikin: chaikin,
};

/**
 * Optional named exports.
 */
export { simplifyDouglasPeucker, simplifyVisvalingam, chaikin };
