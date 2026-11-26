export const MIN_BATCH_PUBLISHES = 5;
export const MAX_BATCH_PUBLISHES = 10;
export const MAX_BATCH_ATTEMPTS = 50;
export const MAX_IN_FLIGHT_BATCH_RENDERS = 1;

export function shouldFillBatch(batch) {
  if (!batch || batch.status !== "active") return false;
  const published = Math.max(0, Number(batch.published) || 0);
  const pending = Math.max(0, Number(batch.pending) || 0);
  const targetMax = Math.max(1, Number(batch.target_max) || MAX_BATCH_PUBLISHES);
  const attempts = Math.max(0, Number(batch.attempts) || 0);
  const maxAttempts = Math.max(1, Number(batch.max_attempts) || MAX_BATCH_ATTEMPTS);
  return published + pending < targetMax && attempts < maxAttempts;
}

export function batchCompletionStatus(batch) {
  const published = Math.max(0, Number(batch?.published) || 0);
  const targetMin = Math.max(1, Number(batch?.target_min) || MIN_BATCH_PUBLISHES);
  return published >= targetMin ? "completed" : "underfilled";
}
