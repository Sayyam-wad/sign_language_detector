// Feature extraction, ported from asl/features.py. Must stay numerically identical:
// tests/test_web_parity.py runs web/parity_check.mjs against cases exported by Python.

export const FEATURE_VERSION = 2;
const WRIST = 0;
const FINGERS = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16], [17, 18, 19, 20]];
const TIPS = [4, 8, 12, 16, 20];

/** Wrist at origin, palm length 1, left hands mirrored. points: 21 x [x, y, z] in pixel units. */
export function normalizeLandmarks(points, handedness = "Right") {
  const p = points.map(([x, y, z]) => [handedness === "Left" ? -x : x, y, z]);
  const w = p[WRIST].slice();
  for (const q of p) { q[0] -= w[0]; q[1] -= w[1]; q[2] -= w[2]; }
  let palm = Math.hypot(p[9][0], p[9][1]);
  if (palm < 1e-6) palm = Math.max(...p.map((q) => Math.hypot(q[0], q[1]))) || 1;
  return p.map((q) => q.map((v) => v / palm));
}

function angle(a, b, c) {
  const v1 = [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const v2 = [c[0] - b[0], c[1] - b[1], c[2] - b[2]];
  const dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2];
  const n = Math.hypot(...v1) * Math.hypot(...v2) + 1e-9;
  return Math.acos(Math.min(1, Math.max(-1, dot / n)));
}

/** 85 features: 60 coordinates, 15 joint angles, 10 fingertip distances. */
export function landmarkFeatures(points, handedness = "Right") {
  const p = normalizeLandmarks(points, handedness);
  const out = [];
  for (let i = 1; i < 21; i++) out.push(p[i][0], p[i][1], p[i][2]);
  for (const [base, j1, j2, tip] of FINGERS) {
    const chain = [WRIST, base, j1, j2, tip];
    for (const k of [1, 2, 3]) out.push(angle(p[chain[k - 1]], p[chain[k]], p[chain[k + 1]]));
  }
  for (let i = 0; i < TIPS.length; i++) {
    for (let j = i + 1; j < TIPS.length; j++) {
      out.push(Math.hypot(p[TIPS[i]][0] - p[TIPS[j]][0], p[TIPS[i]][1] - p[TIPS[j]][1]));
    }
  }
  return out;
}
