import numpy as np
import pytest

from asl.features import N_FEATURES, landmark_features, normalize_landmarks
from asl.labels import CLASSES, LETTER, LETTERS, PHRASE, PHRASES, output_label
from tests.synthetic import hand_points

CURLS = np.array([0.2, 0.0, 0.9, 0.9, 0.1])


def test_feature_length():
    assert landmark_features(hand_points(CURLS)).shape == (N_FEATURES,)


def test_translation_and_scale_invariance():
    a = landmark_features(hand_points(CURLS, scale=60, offset=(100, 100)))
    b = landmark_features(hand_points(CURLS, scale=180, offset=(500, 300)))
    np.testing.assert_allclose(a, b, atol=1e-5)


def test_left_hand_is_mirrored_onto_right():
    right = landmark_features(hand_points(CURLS), "Right")
    left = landmark_features(hand_points(CURLS, left=True), "Left")
    np.testing.assert_allclose(right, left, atol=1e-5)


def test_orientation_is_preserved():
    # H/U-style pairs differ by orientation, so rotation must change the features.
    up = landmark_features(hand_points(CURLS, rotation=0.0))
    sideways = landmark_features(hand_points(CURLS, rotation=np.pi / 2))
    assert np.abs(up - sideways).max() > 0.5


def test_normalized_palm_length_is_one():
    p = normalize_landmarks(hand_points(CURLS, scale=123))
    assert np.allclose(p[0], 0) and np.isclose(np.linalg.norm(p[9, :2]), 1.0)


def test_bad_shape_rejected():
    with pytest.raises(ValueError):
        landmark_features(np.zeros((20, 3)))


def test_labels_cover_alphabet_and_phrases():
    assert LETTERS == sorted("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    assert "HELLO" in PHRASES and len(CLASSES) == 41


def test_letter_a_stays_a_in_letter_mode():
    # The old ambiguity table turned class 0 (A) into "S" in letter mode.
    assert output_label(0, LETTER) == "A"


@pytest.mark.parametrize("phrase,letter", [("NO", "C"), ("OKAY", "O"), ("PEACE", "V")])
def test_look_alikes_resolve_by_mode(phrase, letter):
    from asl.labels import NAME_TO_ID
    assert output_label(NAME_TO_ID[phrase], LETTER) == letter
    assert output_label(NAME_TO_ID[letter], PHRASE) == phrase
    assert output_label(NAME_TO_ID["HELLO"], LETTER) is None
