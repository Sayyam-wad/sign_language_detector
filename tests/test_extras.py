"""Tests for the sign atlas, no-sign detector, word suggestions and web export."""

import json

import numpy as np

from asl.atlas import CONNECTIONS, load, render
from asl.features import FEATURE_VERSION
from asl.novelty import NoveltyDetector
from asl.recognizer import SignRecognizer, WordBuilder
from asl.synthetic import hand_points, make_dataset
from asl.words import Suggester


def test_atlas_has_every_sign_and_renders():
    from asl.labels import CLASSES
    atlas = load()
    assert set(atlas) == {c.name for c in CLASSES.values()}
    img = render(atlas["L"], 120, "L")
    assert img.shape == (120, 120, 3) and img.max() > 100
    assert len(CONNECTIONS) == 21


def test_novelty_accepts_known_and_rejects_far_poses():
    X, y, _ = make_dataset(n_classes=5)
    det = NoveltyDetector(prototypes_per_class=3).fit(X, y).calibrate(NoveltyDetector(3).fit(X, y).score(X))
    assert det.is_novel(X).mean() <= 0.02
    assert det.is_novel(X + 25.0).all()


def test_recognizer_ignores_novel_poses():
    class Always:
        classes_ = [0, 1]

        def predict_proba(self, X):
            return np.array([[0.9, 0.1]])

    class Novel:
        def is_novel(self, X):
            return np.array([True])

    bundle = {"model": Always(), "classes": [0, 1], "feature_version": FEATURE_VERSION, "novelty": Novel()}
    rec = SignRecognizer(bundle=bundle, smoothing=0.5, min_confidence=0.5)
    pred = rec.update(hand_points(np.zeros(5)))
    assert pred.label is None and pred.best_guess is None


def test_suggestions_complete_and_correct():
    s = Suggester(["HELLO", "HELP", "HELD", "THANK", "THINK", "WATER", "NAME"])
    assert s.suggest("HEL")[:2] == ["HELLO", "HELP"]
    assert "THINK" in s.suggest("THNK") and "THANK" in s.suggest("THNK")
    assert s.suggest("WATR") == ["WATER"]
    assert s.suggest("H") == []


def test_confusable_letters_rank_first():
    # N and M are look-alike hand shapes, so NAMR -> NAME beats NAMR -> NEAR.
    s = Suggester(["NEAR", "NAME"])
    assert s.corrections("NAMR")[0] == "NAME"
    assert Suggester(["MAN", "MAT"]).corrections("NAN")[0] == "MAN"


def test_builder_applies_suggestion():
    wb = WordBuilder()
    wb.text = "SAY HEL"
    assert wb.partial_word == "HEL"
    wb.apply_suggestion("HELLO")
    assert wb.text == "SAY HELLO "
    assert wb.partial_word == ""


def test_default_word_list_loads():
    s = Suggester.default()
    assert "HELLO" in s and "THE" in s


def test_web_export_roundtrip(tmp_path):
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    from asl.web_export import export
    X, y, _ = make_dataset(n_classes=4)
    pipe = make_pipeline(StandardScaler(), MLPClassifier((16,), max_iter=300, random_state=0)).fit(X, y)
    nov = NoveltyDetector(2).fit(X, y).calibrate(np.array([1.0, 2.0]))
    data = export(pipe, nov, tmp_path / "m.json")
    loaded = json.loads((tmp_path / "m.json").read_text())
    assert loaded["classes"] == [int(c) for c in pipe.classes_]
    assert len(loaded["layers"]) == 2 and len(data["parity_cases"]) == 4
