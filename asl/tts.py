"""Non-blocking text-to-speech.

The old app called pyttsx3's runAndWait() on the video thread, freezing the
camera feed while speaking. Speech now runs on a background worker.
"""

from __future__ import annotations

import queue
import threading

from asl import config


class Speaker:
    def __init__(self, rate: int = config.SPEECH_RATE):
        self.rate = rate
        self._q: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            import pyttsx3
        except ImportError:
            print("pyttsx3 not installed: speech disabled")
            return
        while True:
            text = self._q.get()
            if text is None:
                return
            try:
                # A fresh engine per utterance avoids pyttsx3's run-loop hangs on Windows.
                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:  # audio device problems should never crash the app
                print(f"Speech error: {e}")

    def say(self, text: str) -> None:
        if text.strip():
            self._q.put(text.strip())

    def close(self) -> None:
        self._q.put(None)
