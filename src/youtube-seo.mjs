const BASE_TAGS = [
  "GTA 6", "GTA VI", "Grand Theft Auto VI", "GTA 6 gameplay",
  "GTA 6 clips", "GTA VI gameplay", "GTA 6 Shorts", "gaming shorts", "VI RUSH",
];

const ANGLE_TAGS = {
  police: ["GTA 6 police chase", "GTA 6 cops"],
  vehicle: ["GTA 6 cars", "GTA 6 driving"],
  comedy: ["GTA 6 funny moments", "GTA 6 fails"],
  discovery: ["GTA 6 secrets", "GTA 6 hidden details"],
  explosion: ["GTA 6 action", "GTA 6 explosions"],
  combat: ["GTA 6 combat", "GTA 6 fights"],
  detail: ["GTA 6 gameplay details", "GTA 6 graphics"],
  mission: ["GTA 6 missions", "GTA 6 heists"],
  character: ["GTA 6 characters"],
  mature: ["GTA 6 nightlife"],
  relationship: ["GTA 6 relationships"],
};

const ANGLE_HASHTAGS = {
  police: "#GTA6Police",
  vehicle: "#GTA6Cars",
  comedy: "#GTA6Funny",
  discovery: "#GTA6Secrets",
  explosion: "#GTA6Action",
  combat: "#GTA6Combat",
  detail: "#GTA6Details",
  mission: "#GTA6Missions",
  character: "#GTA6Characters",
  mature: "#GTA6Nightlife",
  relationship: "#GTA6Story",
};

const GENERIC_TOPICS = new Set([
  "gta", "gta 6", "gta vi", "grand theft auto", "grand theft auto vi",
  "gameplay", "gta gameplay", "gta 6 gameplay", "gta vi gameplay",
  "clip", "highlight", "moment", "stream", "stream clip",
]);

function clean(value, max = 240) {
  return String(value ?? "").replace(/[\r\n\t]+/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}

function getTopic(originalTitle) {
  return clean(originalTitle)
    .replace(/^(?:grand theft auto\s*(?:vi|6)?|gta\s*(?:vi|6)?)\s*[:|—–-]*\s*/i, "")
    .replace(/\s+(?:in|at|during)\s+gta\s*(?:vi|6)\s*$/i, "")
    .replace(/^[|:—–-]+\s*/, "")
    .trim();
}

function fitTitle(value, maxLength) {
  const text = clean(value, 500);
  if (text.length <= maxLength) return text;
  const clipped = text.slice(0, maxLength);
  const boundary = clipped.lastIndexOf(" ");
  return (boundary >= Math.floor(maxLength * 0.65) ? clipped.slice(0, boundary) : clipped).trim();
}

function appendUnique(tags, candidate) {
  const tag = clean(candidate, 100);
  if (!tag || tags.some((item) => item.toLowerCase() === tag.toLowerCase())) return;
  const used = tags.reduce((sum, item) => sum + item.length + 1, 0);
  if (tags.length < 20 && used + tag.length <= 480) tags.push(tag);
}

/**
 * Build truthful YouTube metadata from known Twitch source fields.
 * The source title is preserved in its original language; no event is inferred
 * from footage that the Worker has not semantically analysed.
 */
export function buildYouTubeMetadata({
  originalTitle = "",
  creatorName = "",
  sourceUrl = "",
  angle = "moment",
  hook = "",
} = {}) {
  const original = clean(originalTitle, 180) || "GTA 6 clip";
  const creator = clean(creatorName, 80);
  const topic = getTopic(original);
  const usefulTopic = topic.length >= 3 && !GENERIC_TOPICS.has(topic.toLowerCase());
  const titleSuffix = " | VI RUSH #Shorts";
  const hookText = clean(hook, 40);
  const titleBase = usefulTopic
    ? "GTA 6: " + (hookText ? hookText + " — " : "") + topic
    : creator ? "GTA 6 Stream Clip: " + (hookText ? hookText + " — " : "") + creator : "GTA 6 Gameplay Clip";
  const title = fitTitle(titleBase, 100 - titleSuffix.length) + titleSuffix;

  const descriptionParts = [
    "A Grand Theft Auto VI (GTA 6) gameplay clip from " + (creator || "a Twitch creator") + ".",
    hookText ? hookText + "." : "",
    'Original clip title: "' + original + '".',
    "Follow VI RUSH for more GTA VI gameplay clips and creator highlights.",
  ].filter(Boolean);
  if (sourceUrl) descriptionParts.push("Original source: " + clean(sourceUrl, 500));
  const hashtags = ["#GTA6", "#GTAVI"];
  if (ANGLE_HASHTAGS[angle]) hashtags.push(ANGLE_HASHTAGS[angle]);
  hashtags.push("#GamingShorts", "#Shorts");
  descriptionParts.push(hashtags.join(" "));
  const description = descriptionParts.join("\n\n").slice(0, 5000);

  const tags = [];
  for (const tag of BASE_TAGS) appendUnique(tags, tag);
  for (const tag of ANGLE_TAGS[angle] || []) appendUnique(tags, tag);
  if (usefulTopic) {
    appendUnique(tags, original);
    // Only prefix a translated-language keyword phrase when it is Latin-script;
    // never fabricate broken combinations such as "GTA 6 радует".
    if (topic.length <= 65 && /\\p{Script=Latin}/u.test(topic)) {
      appendUnique(tags, "GTA 6 " + topic);
    }
  }
  if (creator) {
    appendUnique(tags, creator);
    appendUnique(tags, creator + " Twitch");
  }

  return { title, description, tags, hashtags, topic: usefulTopic ? topic : "" };
}
