"""Word suggestions for fingerspelling.

Spelling letter by letter is slow and one misread letter spoils a word, so
while you spell, the app offers up to three words (press 1, 2 or 3 to take
one):

  * completions of what you've spelled so far, most frequent first
    ("HEL" -> HELP, HELLO, HELD)
  * corrections when nothing starts with it: words one or two edits away,
    preferring substitutions between letters the classifier tends to mix up
    ("HELLP" -> HELLO, HELP)

Nothing is changed automatically; suggestions are only applied on a keypress.
Word list: the 20,000 most frequent English words from wordfreq
(see asl/assets/README.md for the licence).
"""

from __future__ import annotations

import bisect
from functools import lru_cache
from pathlib import Path

WORDS_PATH = Path(__file__).resolve().parent / "assets" / "words.txt"

# Letter pairs whose static hand shapes are close (cheaper substitutions).
CONFUSABLE = {frozenset(p) for p in ["MN", "MS", "NS", "AS", "AE", "ES", "ET", "AT", "UV", "UR", "VK", "KP",
                                     "GH", "GQ", "PQ", "IJ", "DZ", "OC", "XE", "WF"]}


class Suggester:
    def __init__(self, words: list[str]):
        self.rank = {w: i for i, w in enumerate(words)}  # lower = more frequent
        self.sorted = sorted(self.rank)

    @classmethod
    @lru_cache(maxsize=1)
    def default(cls) -> Suggester:
        words = WORDS_PATH.read_text().split() if WORDS_PATH.exists() else []
        return cls([w.upper() for w in words])

    def __contains__(self, word: str) -> bool:
        return word.upper() in self.rank

    def completions(self, prefix: str, n: int = 3) -> list[str]:
        prefix = prefix.upper()
        i = bisect.bisect_left(self.sorted, prefix)
        found = []
        while i < len(self.sorted) and self.sorted[i].startswith(prefix):
            if self.sorted[i] != prefix or len(prefix) > 1:
                found.append(self.sorted[i])
            i += 1
        return sorted(found, key=self.rank.__getitem__)[:n]

    def corrections(self, word: str, n: int = 3) -> list[str]:
        word = word.upper()
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        scored: dict[str, float] = {}

        def edits(w):
            for i in range(len(w) + 1):
                a, b = w[:i], w[i:]
                if b:
                    yield a + b[1:], 1.0                       # deletion (an extra letter got added)
                    for c in letters:
                        if c != b[0]:
                            cost = 0.5 if frozenset((c, b[0])) in CONFUSABLE else 1.0
                            yield a + c + b[1:], cost            # substitution
                if len(b) > 1:
                    yield a + b[1] + b[0] + b[2:], 1.0          # transposition
                for c in letters:
                    yield a + c + b, 1.0                        # insertion (a letter was missed)

        for cand, cost in edits(word):
            if cand in self.rank:
                scored[cand] = min(scored.get(cand, 9), cost)
        if not scored and len(word) > 4:
            for c1, cost1 in edits(word):
                for cand, cost2 in edits(c1):
                    if cand in self.rank:
                        scored[cand] = min(scored.get(cand, 9), cost1 + cost2)
        return sorted(scored, key=lambda w: (scored[w], self.rank[w]))[:n]

    def suggest(self, partial: str, n: int = 3) -> list[str]:
        if len(partial) < 2 or not partial.isalpha():
            return []
        out = self.completions(partial, n)
        if partial.upper() in self.rank and partial.upper() not in out:
            out = [partial.upper()] + out[: n - 1]
        if len(out) < n and len(partial) >= 3:
            out += [w for w in self.corrections(partial, n) if w not in out]
        return out[:n]
