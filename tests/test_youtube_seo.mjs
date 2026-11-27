import test from "node:test";
import assert from "node:assert/strict";
import { buildYouTubeMetadata } from "../src/youtube-seo.mjs";

test("keeps the original German clip title while making a complete VI RUSH title", () => {
  const metadata = buildYouTubeMetadata({
    originalTitle: "Leute fallen auf Wutköder Video rein",
    creatorName: "MontanaBlack88",
    sourceUrl: "https://www.twitch.tv/example/clip/ExampleSlug",
    angle: "moment",
  });
  assert.ok(metadata.title.includes("Leute fallen auf Wutköder Video rein"));
  assert.ok(metadata.title.includes("VI RUSH"));
  assert.ok(metadata.description.includes('Original clip title: "Leute fallen auf Wutköder Video rein".'));
  assert.ok(metadata.description.includes("MontanaBlack88"));
  assert.ok(metadata.tags.includes("Leute fallen auf Wutköder Video rein"));
  assert.ok(!metadata.tags.includes("GTA 6 leute"));
  assert.ok(!metadata.tags.includes("GTA 6 fallen"));
});

test("keeps a non-Latin title intact and does not manufacture single-word keyword tags", () => {
  const metadata = buildYouTubeMetadata({
    originalTitle: "Gta6 радует",
    creatorName: "evelone2004",
    angle: "moment",
  });
  assert.ok(metadata.title.includes("радует"));
  assert.ok(metadata.description.includes('Original clip title: "Gta6 радует".'));
  assert.ok(metadata.tags.includes("Gta6 радует"));
  assert.ok(!metadata.tags.includes("GTA 6 радует"));
  assert.ok(metadata.tags.includes("evelone2004 Twitch"));
});

test("adds supported topic tags for an English police title", () => {
  const metadata = buildYouTubeMetadata({
    originalTitle: "Police chase goes wrong in GTA 6",
    creatorName: "ExampleStreamer",
    angle: "police",
  });
  assert.match(metadata.title, /Police chase goes wrong/);
  assert.doesNotMatch(metadata.title, /wrong in GTA 6/);
  assert.ok(metadata.tags.includes("GTA 6 police chase"));
  assert.ok(metadata.hashtags.includes("#GTA6Police"));
  assert.ok(metadata.description.includes("#GTA6Police"));
});

test("respects YouTube title and tag limits and has safe fallbacks", () => {
  const metadata = buildYouTubeMetadata({
    originalTitle: "A".repeat(180),
    creatorName: "Creator",
  });
  assert.ok(metadata.title.length <= 100);
  assert.ok(metadata.tags.length <= 20);
  assert.ok(metadata.tags.reduce((sum, tag) => sum + tag.length + 1, 0) <= 480);
  assert.ok(metadata.description.length <= 5000);

  const fallback = buildYouTubeMetadata({});
  assert.ok(fallback.title.startsWith("GTA 6 Gameplay Clip"));
  assert.ok(fallback.hashtags.includes("#Shorts"));
});

test("uses an optional supplied hook in the same shared SEO package", () => {
  const metadata = buildYouTubeMetadata({
    originalTitle: "Police chase in GTA 6",
    creatorName: "ExampleStreamer",
    hook: "Unexpected turn",
    angle: "police",
  });
  assert.match(metadata.title, /Unexpected turn/);
  assert.ok(metadata.description.includes("Unexpected turn."));
});
