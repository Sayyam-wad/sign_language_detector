"""The browser demo must compute the same features and probabilities as Python."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
@pytest.mark.parametrize("which", ["fresh", "committed"])
def test_javascript_matches_python(tmp_path, which):
    if which == "committed":
        model_json = ROOT / "web" / "model.json"
        if not model_json.exists():
            pytest.skip("no exported web model")
    else:
        from sklearn.neural_network import MLPClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        from asl.novelty import NoveltyDetector
        from asl.synthetic import make_dataset
        from asl.web_export import export
        X, y, _ = make_dataset(n_classes=6)
        pipe = make_pipeline(StandardScaler(), MLPClassifier((32, 16), max_iter=400, random_state=0)).fit(X, y)
        nov = NoveltyDetector(3).fit(X, y).calibrate(np.array([1.0]))
        model_json = tmp_path / "web" / "model.json"
        export(pipe, nov, model_json)
    result = subprocess.run(["node", str(ROOT / "web" / "parity_check.mjs"), str(model_json)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
