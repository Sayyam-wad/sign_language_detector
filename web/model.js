// Classifier, "no sign" detector, smoothing and word building for the browser demo.
// Mirrors asl/recognizer.py and asl/novelty.py; weights come from web/model.json.

import { landmarkFeatures } from "./features.js";

export class Model {
  constructor(data) {
    this.d = data;
    this.classes = data.classes;
  }

  static async load(url = "model.json") {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`could not load ${url}`);
    return new Model(await res.json());
  }

  /** Class probabilities for a feature vector (StandardScaler -> ReLU MLP -> softmax). */
  probs(x) {
    const { mean, scale } = this.d.scaler;
    let h = x.map((v, i) => (v - mean[i]) / scale[i]);
    const layers = this.d.layers;
    layers.forEach((layer, li) => {
      const next = layer.b.slice();
      for (let o = 0; o < next.length; o++) {
        const row = layer.W[o];
        let s = next[o];
        for (let i = 0; i < h.length; i++) s += row[i] * h[i];
        next[o] = s;
      }
      h = li < layers.length - 1 ? next.map((v) => Math.max(0, v)) : next;
    });
    const m = Math.max(...h);
    const e = h.map((v) => Math.exp(v - m));
    const z = e.reduce((a, b) => a + b, 0);
    return e.map((v) => v / z);
  }

  /** Distance to the nearest training prototype (bigger = less like any trained sign). */
  novelty(x) {
    const n = this.d.novelty;
    if (!n) return 0;
    const zx = x.map((v, i) => (v - n.mean[i]) / n.scale[i]);
    let best = Infinity;
    for (const p of n.prototypes) {
      let s = 0;
      for (let i = 0; i < p.length; i++) { const d = zx[i] - p[i]; s += d * d; }
      if (s < best) best = s;
    }
    return Math.sqrt(best);
  }

  isNovel(x) {
    return this.d.novelty ? this.novelty(x) > this.d.novelty.threshold : false;
  }

  /** Output labels available in a mode, and class -> label mapping (look-alikes merged). */
  modeLabels(mode) {
    const map = this.d.labels[mode];
    return [...new Set(map.filter(Boolean))].sort();
  }
}

export class Recognizer {
  constructor(model, { smoothing = 0.6, minConfidence = 0.55 } = {}) {
    Object.assign(this, { model, smoothing, minConfidence });
    this.state = null;
    this.stateMode = null;
  }

  reset() { this.state = null; }

  update(points, handedness, mode) {
    if (!points) { this.reset(); return { label: null, confidence: 0, best: null, top: [] }; }
    const labels = this.model.modeLabels(mode);
    const x = landmarkFeatures(points, handedness);
    let p = new Array(labels.length).fill(0);
    if (!this.model.isNovel(x)) {
      const probs = this.model.probs(x);
      const map = this.model.d.labels[mode];
      probs.forEach((v, i) => { if (map[i]) p[labels.indexOf(map[i])] += v; });
    }
    if (!this.state || this.stateMode !== mode || this.state.length !== p.length) {
      this.state = p; this.stateMode = mode;
    } else {
      this.state = this.state.map((s, i) => this.smoothing * s + (1 - this.smoothing) * p[i]);
    }
    const order = this.state.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]);
    const top = order.slice(0, 3).map(([v, i]) => [labels[i], v]);
    const [best, conf] = top[0];
    if (conf <= 1e-6) return { label: null, confidence: 0, best: null, top: [] };
    return { label: conf >= this.minConfidence ? best : null, confidence: conf, best, top };
  }
}

export class WordBuilder {
  constructor({ holdSeconds = 1.2, spaceSeconds = 2.0 } = {}) {
    Object.assign(this, { holdSeconds, spaceSeconds });
    this.text = "";
    this.candidate = null; this.since = null; this.armed = true;
    this.noHandSince = null; this.spaceAdded = false;
  }

  holdProgress(now) {
    if (!this.candidate || this.since === null || !this.armed) return 0;
    return Math.min(1, (now - this.since) / this.holdSeconds);
  }

  add(label) {
    if (label.length > 1) {
      if (this.text && !this.text.endsWith(" ")) this.text += " ";
      this.text += label + " ";
    } else this.text += label;
    this.spaceAdded = false;
  }

  update(label, handPresent, now) {
    if (!handPresent) {
      this.candidate = null; this.since = null; this.armed = true;
      if (this.noHandSince === null) this.noHandSince = now;
      else if (!this.spaceAdded && this.text && !this.text.endsWith(" ") && now - this.noHandSince >= this.spaceSeconds) {
        this.text += " "; this.spaceAdded = true;
      }
      return null;
    }
    this.noHandSince = null;
    if (label !== this.candidate) { this.candidate = label; this.since = now; this.armed = true; return null; }
    if (label && this.armed && now - this.since >= this.holdSeconds) { this.add(label); this.armed = false; return label; }
    return null;
  }

  get partialWord() {
    const last = this.text.split(" ").pop();
    return /^[A-Z]+$/.test(last) ? last : "";
  }

  applySuggestion(word) {
    this.text = this.text.slice(0, this.text.length - this.partialWord.length) + word + " ";
    this.spaceAdded = true; this.armed = false;
  }

  backspace() { this.text = this.text.slice(0, -1); }
  clear() { this.text = ""; this.candidate = null; this.armed = true; }
}

/** Prefix completions by word frequency, plus one-edit corrections (as in asl/words.py). */
export class Suggester {
  constructor(words) {
    this.words = words;
    this.rank = new Map(words.map((w, i) => [w, i]));
  }

  static async load(url = "words.txt") {
    try {
      const res = await fetch(url);
      return new Suggester((await res.text()).split(/\s+/).filter(Boolean).map((w) => w.toUpperCase()));
    } catch { return new Suggester([]); }
  }

  suggest(partial, n = 3) {
    if (partial.length < 2) return [];
    const out = [];
    if (this.rank.has(partial)) out.push(partial);
    for (const w of this.words) {
      if (out.length >= n) break;
      if (w.startsWith(partial) && w !== partial) out.push(w);
    }
    if (out.length < n && partial.length >= 3) {
      const A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
      const cands = new Set();
      for (let i = 0; i <= partial.length; i++) {
        const a = partial.slice(0, i), b = partial.slice(i);
        if (b) cands.add(a + b.slice(1));
        for (const c of A) { cands.add(a + c + b); if (b) cands.add(a + c + b.slice(1)); }
      }
      [...cands].filter((w) => this.rank.has(w) && !out.includes(w))
        .sort((x, y) => this.rank.get(x) - this.rank.get(y))
        .slice(0, n - out.length).forEach((w) => out.push(w));
    }
    return out.slice(0, n);
  }
}
