import { Model, Recognizer, Suggester, WordBuilder } from "./model.js";

const TASKS_VERSION = "0.10.21";
const TASKS_URL = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${TASKS_VERSION}`;
const HAND_MODEL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

const CONNECTIONS = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11],
  [11, 12], [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [0, 17], [17, 18], [18, 19], [19, 20]];
const PALM = new Set(["0-5", "5-9", "9-13", "13-17", "0-17"]);
const FINGER_COLORS = ["#ffb450", "#5adc78", "#50c8ff", "#dc78e6", "#ff7878"];
const boneColor = (a, b) => (PALM.has(`${a}-${b}`) ? "#a7b0b9" : FINGER_COLORS[Math.floor((Math.max(a, b) - 1) / 4)]);

const $ = (id) => document.getElementById(id);
const view = $("view");
const ctx = view.getContext("2d");
const grab = document.createElement("canvas");
const grabCtx = grab.getContext("2d", { willReadFrequently: false });

let model, recognizer, suggester, landmarker, video;
const builder = new WordBuilder();
let mode = "LETTER";
let lastTop = "";

function setStatus(text) {
  const el = $("status");
  el.hidden = !text;
  el.textContent = text || "";
}

function drawSkeleton(c, pts, { pad = 0.12, lineWidth = 3, fit = true } = {}) {
  let p = pts;
  if (fit) {  // scale a normalised skeleton into the canvas
    const xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const s = (1 - 2 * pad) * Math.min(c.canvas.width, c.canvas.height) / Math.max(x1 - x0, y1 - y0, 1e-6);
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    p = pts.map(([x, y]) => [(x - cx) * s + c.canvas.width / 2, (y - cy) * s + c.canvas.height / 2]);
  }
  c.lineCap = "round";
  c.lineWidth = lineWidth;
  for (const [a, b] of CONNECTIONS) {
    c.strokeStyle = boneColor(a, b);
    c.beginPath(); c.moveTo(p[a][0], p[a][1]); c.lineTo(p[b][0], p[b][1]); c.stroke();
  }
  c.fillStyle = "#f5f7f9";
  p.forEach(([x, y], i) => {
    c.beginPath(); c.arc(x, y, lineWidth * ([4, 8, 12, 16, 20].includes(i) ? 0.95 : 0.7), 0, Math.PI * 2); c.fill();
  });
}

function tile(name) {
  const fig = document.createElement("figure");
  fig.className = "tile";
  fig.dataset.sign = name;
  const c = document.createElement("canvas");
  c.width = c.height = 160;
  const pts = model.d.atlas[name];
  if (pts) drawSkeleton(c.getContext("2d"), pts, { lineWidth: 4 });
  const cap = document.createElement("figcaption");
  cap.textContent = name.length > 1 ? name.charAt(0) + name.slice(1).toLowerCase() : name;
  fig.append(c, cap);
  return fig;
}

function renderAtlas() {
  const grid = $("atlas");
  grid.replaceChildren(...Object.keys(model.d.atlas)
    .sort((a, b) => (a.length > 1) - (b.length > 1) || a.localeCompare(b))
    .map(tile));
}

function textToSigns(text) {
  const phrases = new Set(Object.keys(model.d.atlas).filter((k) => k.length > 1));
  const words = text.toUpperCase().split(/\s+/).filter(Boolean);
  const out = [];
  for (let i = 0; i < words.length;) {
    const three = words.slice(i, i + 3).join(" "), two = words.slice(i, i + 2).join(" ");
    if (phrases.has(three)) { out.push(three); i += 3; }
    else if (phrases.has(two)) { out.push(two); i += 2; }
    else if (phrases.has(words[i])) { out.push(words[i]); i += 1; }
    else { out.push(...[...words[i]].filter((ch) => /[A-Z]/.test(ch))); i += 1; }
  }
  return out;
}

function renderText() {
  $("text").textContent = builder.text;
  const list = mode === "LETTER" ? suggester.suggest(builder.partialWord) : [];
  $("suggestions").replaceChildren(...list.map((w, i) => {
    const b = document.createElement("button");
    b.innerHTML = `<small>${i + 1}</small>`;
    b.append(w);
    b.addEventListener("click", () => { builder.applySuggestion(w); renderText(); });
    return b;
  }));
}

function renderSign(pred, now) {
  const el = $("current");
  const shown = pred.label ?? (pred.best ? pred.best : "–");
  el.textContent = shown.length > 1 ? shown.charAt(0) + shown.slice(1).toLowerCase() : shown;
  el.className = [shown.length > 1 ? "phrase" : "", pred.label ? "" : pred.best ? "unsure" : "none"].join(" ").trim();
  const progress = pred.label ? builder.holdProgress(now) : 0;
  $("hold").style.strokeDashoffset = String(339.3 * (1 - progress));
  const alts = pred.top?.slice(1).filter(([, p]) => p > 0.05).map(([l, p]) => `${l} ${Math.round(p * 100)}%`).join(", ");
  const line = pred.best ? `${Math.round(pred.confidence * 100)}% sure${alts ? ` · next: ${alts}` : ""}` : " ";
  if (line !== lastTop) { $("alternatives").textContent = line; lastTop = line; }
  document.querySelectorAll(".atlas .tile").forEach((t) => t.classList.toggle("hit", t.dataset.sign === pred.label));
}

function setMode(next) {
  mode = next;
  recognizer.reset();
  document.querySelectorAll(".mode button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.mode === mode)));
  renderText();
}

async function startCamera() {
  const btn = $("start");
  btn.disabled = true;
  try {
    setStatus("Loading the hand tracker…");
    const vision = await import(`${TASKS_URL}/vision_bundle.mjs`);
    const files = await vision.FilesetResolver.forVisionTasks(`${TASKS_URL}/wasm`);
    const options = (delegate) => ({
      baseOptions: { modelAssetPath: HAND_MODEL, delegate }, runningMode: "VIDEO", numHands: 1,
      minHandDetectionConfidence: 0.5, minHandPresenceConfidence: 0.5, minTrackingConfidence: 0.5,
    });
    try { landmarker = await vision.HandLandmarker.createFromOptions(files, options("GPU")); }
    catch { landmarker = await vision.HandLandmarker.createFromOptions(files, options("CPU")); }

    setStatus("Waiting for camera permission…");
    video = document.createElement("video");
    video.playsInline = true; video.muted = true;
    video.srcObject = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: "user" } });
    await video.play();
    view.width = grab.width = video.videoWidth;
    view.height = grab.height = video.videoHeight;
    $("intro").hidden = true;
    setStatus("Show one hand");
    requestAnimationFrame(loop);
  } catch (err) {
    btn.disabled = false;
    const denied = err?.name === "NotAllowedError";
    setStatus(denied
      ? "Camera access is blocked. Allow the camera for this site from the address bar, then press Turn on camera."
      : `Couldn't start: ${err?.message ?? err}`);
  }
}

function loop() {
  const now = performance.now() / 1000;
  // Mirror the frame before detection, exactly as the Python app and the training images did.
  grabCtx.save(); grabCtx.translate(grab.width, 0); grabCtx.scale(-1, 1);
  grabCtx.drawImage(video, 0, 0, grab.width, grab.height); grabCtx.restore();
  const result = landmarker.detectForVideo(grab, performance.now());
  ctx.drawImage(grab, 0, 0);

  let points = null, hand = "Right";
  if (result.landmarks?.length) {
    const W = grab.width, H = grab.height;
    points = result.landmarks[0].map((l) => [l.x * W, l.y * H, l.z * W]);
    hand = result.handednesses?.[0]?.[0]?.categoryName ?? "Right";
    drawSkeleton(ctx, points, { fit: false, lineWidth: Math.max(3, W / 160) });
    setStatus("");
  } else {
    setStatus("Show one hand");
  }
  const pred = recognizer.update(points, hand, mode);
  const added = builder.update(pred.label, points !== null, now);
  renderSign(pred, now);
  if (added || builder.text !== $("text").textContent) renderText();
  requestAnimationFrame(loop);
}

function bindControls() {
  $("start").addEventListener("click", startCamera);
  document.querySelectorAll(".mode button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  $("space").addEventListener("click", () => { if (builder.text && !builder.text.endsWith(" ")) builder.text += " "; renderText(); });
  $("back").addEventListener("click", () => { builder.backspace(); renderText(); });
  $("clear").addEventListener("click", () => { builder.clear(); renderText(); });
  $("speak").addEventListener("click", () => {
    if (!builder.text.trim() || !("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    speechSynthesis.speak(new SpeechSynthesisUtterance(builder.text.toLowerCase()));
  });
  $("lookup").addEventListener("input", (e) => $("lookup-result").replaceChildren(...textToSigns(e.target.value).map(tile)));
  document.addEventListener("keydown", (e) => {
    if (e.target instanceof HTMLInputElement || e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (["1", "2", "3"].includes(k)) {
      const w = suggester.suggest(builder.partialWord)[Number(k) - 1];
      if (w && mode === "LETTER") { builder.applySuggestion(w); renderText(); }
    } else if (k === " " && e.target === document.body) { e.preventDefault(); $("space").click(); }
    else if (k === "backspace") $("back").click();
    else if (k === "l") setMode("LETTER");
    else if (k === "p") setMode("PHRASE");
  });
}

async function init() {
  try {
    [model, suggester] = await Promise.all([Model.load("model.json"), Suggester.load("words.txt")]);
  } catch (err) {
    setStatus(`Couldn't load the model: ${err.message}`);
    $("start").disabled = true;
    return;
  }
  recognizer = new Recognizer(model);
  renderAtlas();
  renderText();
  bindControls();
  const acc = model.d.metrics?.web_model_test_accuracy;
  $("model-info").textContent = `This page runs a ${model.d.layers.map((l) => l.b.length).slice(0, -1).join("×")} neural network `
    + `trained on ${model.d.metrics?.n_samples ?? "?"} hand poses (${model.d.classes.length} signs)`
    + (acc ? `, ${(acc * 100).toFixed(1)}% accurate on held-out data from the same signer.` : ".");
}

init();
