/**
 * Detect an explicit self-description in a Twitch channel bio.
 * This is a prioritization hint only, not identity verification. No inference is
 * made from a username, avatar, pronouns, or channel/game category.
 */
export function isSelfDeclaredWomanProfile(user) {
  const description = String(user?.description || "").replace(/\s+/g, " ").trim();
  if (!description) return false;
  const signals = [
    /\bI\s*(?:am|'m|’m)\s+(?:a\s+)?woman\b/i,
    /\bI\s*(?:am|'m|’m)\s+(?:a\s+)?female\s+(?:streamer|creator|gamer)\b/i,
    /\b(?:woman|female)\s+(?:Twitch\s+)?(?:streamer|gaming\s+creator|content\s+creator|gamer)\b/i,
    /\bproud(?:ly)?\s+(?:to\s+be\s+)?(?:a\s+)?woman\b/i,
    /\bwoman-owned\s+(?:channel|brand)\b/i
  ];
  return signals.some((pattern) => pattern.test(description));
}
