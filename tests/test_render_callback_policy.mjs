import test from "node:test";
import assert from "node:assert/strict";
import { canAcceptRenderCallback, isRecoveredStaleJob } from "../src/render-callback-policy.mjs";

test("accepts callbacks for jobs that are still processing", () => {
  assert.equal(canAcceptRenderCallback({ status: "processing" }), true);
  assert.equal(isRecoveredStaleJob({ status: "processing" }), false);
});

test("accepts late results after both the legacy 45-minute and new 24-hour recovery sweep", () => {
  const recovered = {
    status: "failed",
    last_error: "Recovered stale dispatch after 24 hours without callback.",
  };
  assert.equal(isRecoveredStaleJob(recovered), true);
  assert.equal(canAcceptRenderCallback(recovered), true);
  const legacyRecovered = {
    status: "failed",
    last_error: "Recovered stale dispatch after 45 minutes without callback.",
  };
  assert.equal(isRecoveredStaleJob(legacyRecovered), true);
  assert.equal(canAcceptRenderCallback(legacyRecovered), true);
});

test("does not reopen quality-gated, permission, or unrelated failures", () => {
  assert.equal(canAcceptRenderCallback({ status: "failed", last_error: "Quality gate rejected: blurry." }), false);
  assert.equal(canAcceptRenderCallback({ status: "failed", last_error: "YouTube upload failed." }), false);
  assert.equal(canAcceptRenderCallback({ status: "ready" }), false);
  assert.equal(canAcceptRenderCallback(null), false);
});
