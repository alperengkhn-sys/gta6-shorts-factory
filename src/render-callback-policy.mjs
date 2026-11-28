/**
 * A render callback may arrive after the scheduled stale-job recovery only
 * when that recovery marked the job with its explicit timeout reason.
 * This lets verified, late YouTube publications repair their job/batch state
 * without reopening jobs that failed for quality, permissions, or API errors.
 */
export function isRecoveredStaleJob(job) {
  return Boolean(
    job &&
    job.status === "failed" &&
    /^Recovered stale dispatch after (?:45 minutes|24 hours) without callback\.$/.test(String(job.last_error || ""))
  );
}

export function canAcceptRenderCallback(job) {
  return Boolean(job && (job.status === "processing" || isRecoveredStaleJob(job)));
}
