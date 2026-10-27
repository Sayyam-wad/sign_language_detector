"""Class definitions: which folder id is which sign, and how modes resolve them.

Folder ids match the existing dataset layout (`data/<class_id>/*.jpg`).

Some phrase gestures use the same hand shape as a letter (e.g. the NO gesture
and the letter C). The classifier still learns them as separate classes, but at
prediction time each *mode* merges look-alike classes into one output:

  LETTER mode: letters only; a look-alike phrase class counts towards its letter
  PHRASE mode: phrases only; a look-alike letter class counts towards its phrase

So in LETTER mode P("C") = P(class C) + P(class NO), which removes the coin-flip
between two near-identical classes instead of hiding it.
"""

from __future__ import annotations

from dataclasses import dataclass

LETTER, PHRASE = "LETTER", "PHRASE"
MODES = (LETTER, PHRASE)


@dataclass(frozen=True)
class SignClass:
    class_id: int
    name: str
    kind: str  # LETTER or PHRASE
    look_alike: str | None = None  # letter <-> phrase sharing the same hand shape


_PHRASES = {
    3: "I LOVE YOU", 4: "YES", 5: "NO", 6: "OKAY", 7: "THANK YOU", 8: "RESTROOM",
    9: "INFINITE VOID", 10: "HELLO", 11: "PEACE", 12: "GOOD", 13: "BAD",
    14: "TAKE CARE", 15: "HOPE", 16: "I HATE YOU", 17: "BYE",
}
_LETTERS = {
    0: "A", 1: "B", 2: "L", 18: "C", 19: "D", 20: "E", 21: "F", 22: "G", 23: "H",
    24: "I", 25: "J", 26: "K", 27: "M", 28: "N", 29: "O", 30: "P", 31: "Q", 32: "R",
    33: "S", 34: "T", 35: "U", 36: "V", 37: "W", 38: "X", 39: "Y", 40: "Z",
}
# Phrase gesture -> letter with the same static hand shape.
LOOK_ALIKES = {"NO": "C", "OKAY": "O", "THANK YOU": "Y", "INFINITE VOID": "R", "PEACE": "V"}

# J and Z are motion signs; a single-frame classifier only sees their end pose.
MOTION_LETTERS = {"J", "Z"}


def _build() -> dict[int, SignClass]:
    classes = {}
    reverse = {v: k for k, v in LOOK_ALIKES.items()}
    for cid, name in _LETTERS.items():
        classes[cid] = SignClass(cid, name, LETTER, reverse.get(name))
    for cid, name in _PHRASES.items():
        classes[cid] = SignClass(cid, name, PHRASE, LOOK_ALIKES.get(name))
    return dict(sorted(classes.items()))


CLASSES: dict[int, SignClass] = _build()
NAME_TO_ID = {c.name: c.class_id for c in CLASSES.values()}
LETTERS = sorted(c.name for c in CLASSES.values() if c.kind == LETTER)
PHRASES = sorted(c.name for c in CLASSES.values() if c.kind == PHRASE)


def name_of(class_id: int) -> str:
    c = CLASSES.get(int(class_id))
    return c.name if c else str(class_id)


def output_label(class_id: int, mode: str) -> str | None:
    """What a class means in a given mode, or None if it has no meaning there."""
    c = CLASSES.get(int(class_id))
    if c is None:
        return None
    if c.kind == mode:
        return c.name
    return c.look_alike  # e.g. class NO in LETTER mode -> "C"; letter A in PHRASE mode -> None


def mode_outputs(mode: str) -> list[str]:
    return LETTERS if mode == LETTER else PHRASES
