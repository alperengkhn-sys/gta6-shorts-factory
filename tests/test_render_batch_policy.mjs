import test from "node:test";
import assert from "node:assert/strict";
import { MAX_IN_FLIGHT_BATCH_RENDERS,
  MIN_BATCH_PUBLISHES,
  MAX_BATCH_PUBLISHES,
  MAX_BATCH_ATTEMPTS,
  shouldFillBatch,
  batchCompletionStatus,
} from "../src/render-batch-policy.mjs";

test("a failed render creates room for a replacement until ten successful slots are filled", () => {
  assert.equal(shouldFillBatch({
    status: "active", published: 4, pending: 5, target_max: 10,
    attempts: 9, max_attempts: MAX_BATCH_ATTEMPTS
  }), true);
});

test("five successful uploads plus five pending jobs fill the ten-slot batch", () => {
  assert.equal(shouldFillBatch({
    status: "active", published: 5, pending: 5, target_max: 10,
    attempts: 10, max_attempts: MAX_BATCH_ATTEMPTS
  }), false);
});

test("ten successful uploads stop the batch", () => {
  assert.equal(shouldFillBatch({
    status: "active", published: 10, pending: 0, target_max: 10,
    attempts: 14, max_attempts: MAX_BATCH_ATTEMPTS
  }), false);
});

test("attempt ceiling stops endless replacement when the source pool is poor", () => {
  assert.equal(shouldFillBatch({
    status: "active", published: 3, pending: 0, target_max: 10,
    attempts: 50, max_attempts: 50
  }), false);
});

test("five uploads satisfy the minimum; fewer are reported underfilled", () => {
  assert.equal(batchCompletionStatus({ published: 5, target_min: 5 }), "completed");
  assert.equal(batchCompletionStatus({ published: 4, target_min: 5 }), "underfilled");
});

test("production targets remain five minimum and ten maximum", () => {
  assert.equal(MIN_BATCH_PUBLISHES, 5);
  assert.equal(MAX_BATCH_PUBLISHES, 10);
});

test("cross-source fingerprint checks run one publication at a time", () => {
  assert.equal(MAX_IN_FLIGHT_BATCH_RENDERS, 1);
});
