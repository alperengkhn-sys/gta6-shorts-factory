import test from "node:test";
import assert from "node:assert/strict";
import { isSelfDeclaredWomanProfile } from "../src/streamer-priority.mjs";

test("recognizes an explicit first-person woman self-description", () => {
  assert.equal(isSelfDeclaredWomanProfile({description:"I'm a woman who streams GTA VI."}), true);
  assert.equal(isSelfDeclaredWomanProfile({description:"I am a woman and a gamer"}), true);
});

test("recognizes an explicit female streamer/creator description", () => {
  assert.equal(isSelfDeclaredWomanProfile({description:"Female Twitch streamer | GTA VI"}), true);
  assert.equal(isSelfDeclaredWomanProfile({description:"Woman gaming creator"}), true);
});

test("does not infer gender from pronouns, names, or unrelated bio text", () => {
  assert.equal(isSelfDeclaredWomanProfile({description:"she/her | GTA VI and variety"}), false);
  assert.equal(isSelfDeclaredWomanProfile({description:"Looking for women to play GTA with"}), false);
  assert.equal(isSelfDeclaredWomanProfile({description:"GTA VI streamer from Brazil"}), false);
  assert.equal(isSelfDeclaredWomanProfile({display_name:"GTA Girl",description:"Gaming and cars"}), false);
  assert.equal(isSelfDeclaredWomanProfile(null), false);
});
