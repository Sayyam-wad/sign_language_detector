Browser demo, published with GitHub Pages by `.github/workflows/pages.yml`.

- `features.js` and `model.js` are JavaScript ports of `asl/features.py` and `asl/recognizer.py`.
- `model.json` and `words.txt` are written by `python -m asl.train`.
- `parity_check.mjs` checks the JavaScript gives the same numbers as Python (`node web/parity_check.mjs web/model.json`).

Run locally with `python -m http.server -d web 8000` and open http://localhost:8000. Browsers only allow the camera on https or localhost.
