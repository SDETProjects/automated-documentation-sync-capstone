/**
 * Unit tests for PeriodCache (Node.js, no test framework required).
 *
 * Run with: node tests/test_period_cache.js
 *
 * Each test is a simple assert call. A summary is printed at the end.
 * Exits with code 1 if any test fails.
 */
"use strict";

const assert = require("assert");
const { PeriodCache } = require("../src/frontend/period_cache.js");

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  PASS  ${name}`);
    passed++;
  } catch (err) {
    console.error(`  FAIL  ${name}`);
    console.error(`        ${err.message}`);
    failed++;
  }
}

// ---------------------------------------------------------------------------
// Cache miss on cold start
// ---------------------------------------------------------------------------

test("get() returns null for unknown key", () => {
  const cache = new PeriodCache();
  assert.strictEqual(cache.get("2026-08", null), null);
});

test("get() returns null with category on cold start", () => {
  const cache = new PeriodCache();
  assert.strictEqual(cache.get("2026-08", "engineering"), null);
});

// ---------------------------------------------------------------------------
// Cache hit after set()
// ---------------------------------------------------------------------------

test("get() returns stored data after set()", () => {
  const cache = new PeriodCache();
  const data = { projected_total: 30000 };
  cache.set("2026-08", null, data);
  assert.deepStrictEqual(cache.get("2026-08", null), data);
});

test("get() with category returns category-scoped data", () => {
  const cache = new PeriodCache();
  const data = { category: "engineering" };
  cache.set("2026-08", "engineering", data);
  assert.deepStrictEqual(cache.get("2026-08", "engineering"), data);
});

test("overall and category entries are stored independently", () => {
  const cache = new PeriodCache();
  const overall = { scope: "overall" };
  const eng = { scope: "engineering" };
  cache.set("2026-08", null, overall);
  cache.set("2026-08", "engineering", eng);
  assert.deepStrictEqual(cache.get("2026-08", null), overall);
  assert.deepStrictEqual(cache.get("2026-08", "engineering"), eng);
});

// ---------------------------------------------------------------------------
// Invalidation
// ---------------------------------------------------------------------------

test("invalidate() removes all entries for a period", () => {
  const cache = new PeriodCache();
  cache.set("2026-08", null, { x: 1 });
  cache.set("2026-08", "engineering", { x: 2 });
  cache.invalidate("2026-08");
  assert.strictEqual(cache.get("2026-08", null), null);
  assert.strictEqual(cache.get("2026-08", "engineering"), null);
});

test("invalidate() does not remove other periods", () => {
  const cache = new PeriodCache();
  cache.set("2026-08", null, { a: 1 });
  cache.set("2026-07", null, { b: 2 });
  cache.invalidate("2026-08");
  assert.deepStrictEqual(cache.get("2026-07", null), { b: 2 });
});

test("invalidate() on non-existent period is a no-op", () => {
  const cache = new PeriodCache();
  assert.doesNotThrow(() => cache.invalidate("2025-01"));
});

// ---------------------------------------------------------------------------
// clear()
// ---------------------------------------------------------------------------

test("clear() removes all entries", () => {
  const cache = new PeriodCache();
  cache.set("2026-08", null, { x: 1 });
  cache.set("2026-07", null, { y: 2 });
  cache.clear();
  assert.strictEqual(cache.get("2026-08", null), null);
  assert.strictEqual(cache.get("2026-07", null), null);
});

test("size is 0 after clear()", () => {
  const cache = new PeriodCache();
  cache.set("2026-08", null, {});
  cache.clear();
  assert.strictEqual(cache.size, 0);
});

// ---------------------------------------------------------------------------
// Size tracking
// ---------------------------------------------------------------------------

test("size reflects number of stored entries", () => {
  const cache = new PeriodCache();
  assert.strictEqual(cache.size, 0);
  cache.set("2026-08", null, {});
  assert.strictEqual(cache.size, 1);
  cache.set("2026-08", "engineering", {});
  assert.strictEqual(cache.size, 2);
});

// ---------------------------------------------------------------------------
// Financial data NOT in sessionStorage (policy verification)
// ---------------------------------------------------------------------------

test("PeriodCache does not call sessionStorage.setItem or .getItem", () => {
  // Policy check (Design Review revision item 3): financial data must not be
  // written to sessionStorage. Allow the word in comments (documentation) but
  // disallow API calls like sessionStorage.setItem(...) or sessionStorage.getItem.
  const fs = require("fs");
  const src = fs.readFileSync(
    require("path").join(__dirname, "../src/frontend/period_cache.js"),
    "utf8"
  );
  const hasSetItem  = /sessionStorage\s*\.\s*setItem/.test(src);
  const hasGetItem  = /sessionStorage\s*\.\s*getItem/.test(src);
  const hasRemoveItem = /sessionStorage\s*\.\s*removeItem/.test(src);
  assert.ok(
    !hasSetItem && !hasGetItem && !hasRemoveItem,
    "PeriodCache must not call sessionStorage.setItem/getItem/removeItem"
  );
});

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

console.log(`\nResults: ${passed} passed, ${failed} failed\n`);
if (failed > 0) process.exit(1);
