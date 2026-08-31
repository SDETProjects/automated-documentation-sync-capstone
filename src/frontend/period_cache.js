/**
 * PeriodCache — client-side in-memory cache for forecast API responses.
 *
 * Design Review constraint (revision item 3): financial data (spend amounts,
 * projected totals, budget values) MUST NOT be stored in sessionStorage or
 * localStorage. This cache uses an in-memory Map only, scoped to the current
 * JavaScript runtime lifetime (i.e. until the page is unloaded or reloaded).
 *
 * Cache keys are "{period}:{category}" where category defaults to "overall"
 * when null/undefined is passed. This allows independent caching of the
 * overall view and each per-category view for the same period (FR-3, NFR-2).
 *
 * Usage:
 *   const cache = new PeriodCache();
 *   cache.set("2026-08", null, responseData);
 *   const data = cache.get("2026-08", null);  // returns responseData
 *   cache.invalidate("2026-08");              // clears all entries for period
 *   cache.clear();                            // clears entire cache
 */
class PeriodCache {
  constructor() {
    /** @type {Map<string, object>} */
    this._store = new Map();
  }

  /**
   * Build the cache key for a period + optional category.
   * @param {string} period - YYYY-MM period string.
   * @param {string|null|undefined} category - Category ID or null for overall.
   * @returns {string}
   */
  _key(period, category) {
    return `${period}:${category ?? "overall"}`;
  }

  /**
   * Retrieve a cached forecast response.
   * @param {string} period
   * @param {string|null|undefined} category
   * @returns {object|null} Cached response object, or null on cache miss.
   */
  get(period, category) {
    return this._store.get(this._key(period, category)) ?? null;
  }

  /**
   * Store a forecast response in the cache.
   * @param {string} period
   * @param {string|null|undefined} category
   * @param {object} data - The API response object to cache.
   */
  set(period, category, data) {
    this._store.set(this._key(period, category), data);
  }

  /**
   * Remove all cached entries for a given period (all categories).
   * Called by the chart's "Refresh" button handler.
   * @param {string} period
   */
  invalidate(period) {
    for (const key of this._store.keys()) {
      if (key.startsWith(`${period}:`)) {
        this._store.delete(key);
      }
    }
  }

  /**
   * Clear the entire cache.
   */
  clear() {
    this._store.clear();
  }

  /**
   * Return the number of entries currently in the cache (for diagnostics).
   * @returns {number}
   */
  get size() {
    return this._store.size;
  }
}

// Export for Node.js (tests) and browser (module script).
if (typeof module !== "undefined" && module.exports) {
  module.exports = { PeriodCache };
} else {
  window.PeriodCache = PeriodCache;
}
