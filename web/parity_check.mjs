// Checks that the JavaScript features + network reproduce the Python numbers.
// Usage: node web/parity_check.mjs web/model.json   (exit code 1 on mismatch)
import { readFileSync } from "node:fs";
import { landmarkFeatures } from "./features.js";
import { Model } from "./model.js";

const data = JSON.parse(readFileSync(process.argv[2] ?? new URL("model.json", import.meta.url), "utf8"));
const model = new Model(data);
let worstFeat = 0, worstProb = 0, worstNov = 0;
for (const c of data.parity_cases) {
  const x = landmarkFeatures(c.points, c.handedness);
  // Python rounds the points to 4 decimals before exporting, so compare against its features
  // recomputed from the same rounded points: the tolerance covers float32 vs float64 only.
  x.forEach((v, i) => { worstFeat = Math.max(worstFeat, Math.abs(v - c.features[i])); });
  model.probs(c.features).forEach((v, i) => { worstProb = Math.max(worstProb, Math.abs(v - c.probs[i])); });
  if (c.novelty !== null) worstNov = Math.max(worstNov, Math.abs(model.novelty(c.features) - c.novelty));
}
const ok = worstFeat < 1e-4 && worstProb < 1e-4 && worstNov < 1e-3;
console.log(JSON.stringify({ cases: data.parity_cases.length, worstFeat, worstProb, worstNov, ok }));
process.exit(ok ? 0 : 1);
