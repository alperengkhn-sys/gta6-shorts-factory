import test from "node:test";
import assert from "node:assert/strict";
import { canAcceptRenderCallback, isRecoveredStaleJob } from "../src/render-callback-policy.mjs";

test("accepts callbacks for jobs that are still processing", () => {
  assert.equal(canAcceptRenderCallback({ status: "processing" }), true);
  assert.equal(isRecoveredStaleJob({ status: "processing" }), false);
});

test("accepts a late result only for the exact 24-hour stale recovery reason", () => {
  const recovered = {
    status: "failed",
    last_error: "Recovered stale dispatch after 24 hours without callback.",
  };
  assert.equal(isRecoveredStaleJob(recovered), true);
  assert.equal(canAcceptRenderCallback(recovered), true);
});

test("does not reopen quality-gated, permission, or unrelated failures", () => {
  assert.equal(canAcceptRenderCallback({ status: "failed", last_error: "Quality gate rejected: blurry." }), false);
  assert.equal(canAcceptRenderCallback({ status: "failed", last_error: "YouTube upload failed." }), false);
  assert.equal(canAcceptRenderCallback({ status: "ready" }), false);
  assert.equal(canAcceptRenderCallback(null), false);
});
