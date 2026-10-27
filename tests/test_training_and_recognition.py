import numpy as np
import pytest

from asl.dataset import group_for
from asl.labels import LETTER, NAME_TO_ID, PHRASE, name_of
from asl.recognizer import SignRecognizer, WordBuilder
from asl.synthetic import hand_points, make_dataset


def test_group_names(tmp_path):
    assert group_for(tmp_path / "20260101-101010_5.jpg", 20) == "session:20260101-101010"
    assert group_for(tmp_path / "45.jpg", 20) == "block:2"


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    from asl.features import FEATURE_VERSION
    from asl.train import train
    d = tmp_path_factory.mktemp("run")
    X, y, g = make_dataset()
    np.savez(d / "f.npz", X=X, y=y, groups=g, paths=np.array([""] * len(y)),
             handedness=np.array(["Right"] * len(y)), feature_version=FEATURE_VERSION)
    metrics = train(d / "f.npz", ["logreg", "knn"], cv_folds=3, out_model=d / "m.joblib", report_dir=d / "rep")
    return d, metrics


def test_training_writes_honest_report(trained):
    d, m = trained
    assert m["n_test"] > 0 and m["best_model"] in ("logreg", "knn")
    assert m["test"]["accuracy"] > 0.9  # synthetic classes are well separated
    assert (d / "rep" / "report.md").read_text().startswith("# Evaluation report")
    assert (d / "rep" / "metrics.json").exists()


def test_grouped_split_keeps_groups_apart():
    from asl.train import group_split
    X, y, g = make_dataset(n_groups=5)
    tr, te = group_split(y, g)
    assert not set(g[tr]) & set(g[te])


def test_recognizer_end_to_end(trained):
    d, _ = trained
    rec = SignRecognizer(d / "m.joblib", smoothing=0.5, min_confidence=0.3)
    # Rebuild the prototype of class 0 from the same generator seed.
    rng = np.random.default_rng(0)
    from asl.labels import CLASSES
    protos = {c: (rng.uniform(0, 1, 5), rng.uniform(-0.4, 0.4)) for c in list(CLASSES)[:8]}
    curls, rot = protos[0]
    pred = None
    for _ in range(5):
        pred = rec.update(hand_points(curls, rot), "Right", LETTER)
    assert pred.label == name_of(0)
    assert rec.update(None).label is None


def test_mode_merging_sums_look_alikes():
    class Dummy:
        def predict_proba(self, X):
            return np.array([[0.3, 0.3, 0.4]])
    c, no, hello = NAME_TO_ID["C"], NAME_TO_ID["NO"], NAME_TO_ID["HELLO"]
    from asl.features import FEATURE_VERSION
    rec = SignRecognizer(bundle={"model": Dummy(), "classes": [c, no, hello], "feature_version": FEATURE_VERSION},
                         smoothing=0, min_confidence=0.5)
    pts = hand_points(np.zeros(5))
    letter = rec.update(pts, "Right", LETTER)
    assert letter.label == "C" and np.isclose(letter.confidence, 0.6)   # C + NO; HELLO has no letter
    rec.reset()
    phrase = rec.update(pts, "Right", PHRASE)
    assert phrase.label == "NO" and np.isclose(phrase.confidence, 0.6)  # (C + NO) vs HELLO 0.4

    rec.min_confidence = 0.7
    rec.reset()
    assert rec.update(pts, "Right", LETTER).label is None  # not confident enough -> nothing shown


def test_word_builder_hold_repeat_and_space():
    wb = WordBuilder(hold_seconds=1.0, space_seconds=2.0)
    t = 0.0
    for label in "HEL":
        for _ in range(12):
            wb.update(label, True, t)
            t += 0.1
    # second L: lower the hand briefly, then hold L again (the old app could not spell HELLO)
    wb.update(None, False, t)
    for _ in range(12):
        t += 0.1
        wb.update("L", True, t)
    for _ in range(12):
        t += 0.1
        wb.update("O", True, t)
    assert wb.text == "HELLO"
    for _ in range(30):  # no hand for >2 s -> one space
        t += 0.1
        wb.update(None, False, t)
    assert wb.text == "HELLO "
    wb.add("THANK YOU")
    assert wb.text == "HELLO THANK YOU "


def test_held_sign_is_added_only_once():
    wb = WordBuilder(hold_seconds=0.5)
    added = [wb.update("A", True, i * 0.1) for i in range(40)]
    assert added.count("A") == 1 and wb.text == "A"


def test_text_to_sign_tokenizer():
    from asl.app import text_to_sign_tokens
    assert text_to_sign_tokens("hi thank you") == ["H", "I", "THANK YOU"]
    assert text_to_sign_tokens("I love you") == ["I LOVE YOU"]
