"""Real-time ASL recognition app.

    python -m asl.app                      # webcam
    python -m asl.app --source clip.mp4    # a video file
    python -m asl.app --source clip.mp4 --headless   # print the transcript, no window

Keys
  L / P      letter mode / phrase mode
  ENTER      add the current sign now        SPACE      add a space
  BACKSPACE  delete last character           C          clear text
  A          toggle auto-add (hold a sign)   S          speak the text
  1 / 2 / 3  accept a word suggestion
  T          text-to-sign viewer (ESC returns) Q / ESC  quit
"""

from __future__ import annotations

import argparse
import time
from collections import deque
from pathlib import Path

import numpy as np

from asl import config
from asl.labels import LETTER, NAME_TO_ID, PHRASE
from asl.recognizer import SignRecognizer, WordBuilder

MODE_COLORS = {LETTER: (0, 220, 255), PHRASE: (255, 80, 255)}
WINDOW = "ASL Recognition"


_ATLAS: dict | None = None


def sign_image(label: str, size: int = 140, data_dir: Path | None = None, photos: bool = False):
    """Tile for the text-to-sign viewer: a skeleton from the sign atlas (no faces,
    no dataset needed), or with photos=True the first dataset image."""
    import cv2
    global _ATLAS
    if photos and data_dir is not None:
        cid = NAME_TO_ID.get(label)
        files = sorted((data_dir / str(cid)).glob("*.jpg")) if cid is not None else []
        if files:
            return cv2.resize(cv2.imread(str(files[0])), (size, size))
    if _ATLAS is None:
        from asl.atlas import load
        _ATLAS = load()
    if label in _ATLAS:
        from asl.atlas import render
        return render(_ATLAS[label], size, label)
    return None


def text_to_sign_tokens(text: str) -> list[str]:
    """Whole phrases first ("THANK YOU"), then letters."""
    from asl.labels import LETTERS, PHRASES
    words, out, i = text.upper().split(), [], 0
    while i < len(words):
        two = " ".join(words[i:i + 2])
        three = " ".join(words[i:i + 3])
        if three in PHRASES:
            out.append(three)
            i += 3
        elif two in PHRASES:
            out.append(two)
            i += 2
        elif words[i] in PHRASES:
            out.append(words[i])
            i += 1
        else:
            out += [c for c in words[i] if c in LETTERS]
            i += 1
    return out


def draw_text_to_sign(frame_shape, text: str, data_dir: Path, photos: bool = False):
    import cv2
    h, w = frame_shape[:2]
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.putText(canvas, "TEXT TO SIGN  (type; ESC/ENTER to return)", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    cv2.putText(canvas, f"> {text}_", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
    x, y, size = 10, 110, 140
    for token in text_to_sign_tokens(text)[-((w - 10) // (size + 10)) * 2:]:
        tile = sign_image(token, size, data_dir, photos)
        if tile is None:
            tile = np.full((size, size, 3), 40, np.uint8)
            cv2.putText(tile, token[:10], (5, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        if x + size > w:
            x, y = 10, y + size + 10
        if y + size > h:
            break
        canvas[y:y + size, x:x + size] = tile
        x += size + 10
    return canvas


def draw_overlay(frame, mode, pred, builder, auto, fps, now):
    import cv2
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 120), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    text = builder.text[-38:]
    cv2.putText(frame, f"Text: {text}", (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(frame, f"{mode} mode", (10, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.7, MODE_COLORS[mode], 2)
    cv2.putText(frame, f"auto-add {'on' if auto else 'off'} | {fps:4.1f} fps", (w - 260, 66),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)
    if pred.best_guess:
        shown = pred.label or f"{pred.best_guess}?"
        color = (0, 255, 0) if pred.label else (0, 165, 255)
        cv2.putText(frame, shown, (10, 108), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        # confidence bar + hold-to-add progress
        cv2.rectangle(frame, (200, 92), (400, 104), (80, 80, 80), 1)
        cv2.rectangle(frame, (200, 92), (200 + int(200 * pred.confidence), 104), color, -1)
        prog = builder.hold_progress(now) if pred.label else 0
        if prog:
            cv2.rectangle(frame, (200, 108), (200 + int(200 * prog), 114), (255, 255, 0), -1)
        alts = "  ".join(f"{lab} {p:.0%}" for lab, p in pred.top3[1:])
        cv2.putText(frame, alts, (420, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    suggestions = builder.suggestions() if mode == LETTER else []
    if suggestions:
        x = 10
        for i, word in enumerate(suggestions, 1):
            label = f"{i}:{word}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(frame, (x - 4, h - 52), (x + tw + 4, h - 30), (60, 60, 60), -1)
            cv2.putText(frame, label, (x, h - 36), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            x += tw + 16
    cv2.putText(frame, "L/P mode  ENTER add  1-3 word  C clear  S speak  T text->sign  Q quit",
                (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)


def run(source, model_path: Path, headless: bool, mode: str, data_dir: Path) -> str:
    import cv2

    from asl.camera import open_camera, read_frame
    from asl.landmarks import HandDetector

    recognizer = SignRecognizer(model_path)
    builder = WordBuilder()
    is_file = isinstance(source, str) and not source.isdigit()
    if is_file:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise SystemExit(f"Cannot open video {source}")
    else:
        cap = open_camera(int(source))
    speaker = None
    detector = HandDetector(static_image_mode=False)
    typing, typed = False, ""
    times: deque[float] = deque(maxlen=30)
    frame_no = 0
    fps_video = cap.get(cv2.CAP_PROP_FPS) or 30.0
    try:
        while True:
            frame = read_frame(cap, mirror=config.MIRROR and not is_file)
            if frame is None:
                if is_file:
                    break
                continue
            frame_no += 1
            # For video files use the video clock, so results don't depend on processing speed.
            now = frame_no / fps_video if is_file else time.monotonic()
            times.append(time.monotonic())
            fps = (len(times) - 1) / (times[-1] - times[0]) if len(times) > 1 and times[-1] > times[0] else 0.0

            if typing and not headless:
                cv2.imshow(WINDOW, draw_text_to_sign(frame.shape, typed, data_dir))
                key = cv2.waitKey(1) & 0xFF
                if key in (27, 9, 13):  # ESC, TAB or ENTER: back to recognition
                    typing = False
                elif key == 8:
                    typed = typed[:-1]
                elif 32 <= key < 127:
                    typed += chr(key)
                continue

            hand = detector.detect(frame)
            pred = recognizer.update(hand.points if hand else None, hand.handedness if hand else "Right", mode)
            added = builder.update(pred.label, hand is not None, now)
            if headless:
                if added:
                    print(f"[{now:6.2f}s] + {added!r:>14}   text: {builder.text!r}")
                continue

            if hand is not None:
                detector.draw(frame, hand)
                x1, y1, x2, y2 = hand.bbox()
                cv2.rectangle(frame, (x1 - 10, y1 - 10), (x2 + 10, y2 + 10), (0, 255, 0), 2)
            draw_overlay(frame, mode, pred, builder, builder.auto_commit, fps, now)
            cv2.imshow(WINDOW, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            elif key in (ord("l"), ord("p")):
                mode = LETTER if key == ord("l") else PHRASE
                recognizer.reset()
            elif key == 13:
                builder.commit(pred.label or pred.best_guess)
            elif key == 32:
                builder.space()
            elif key == 8:
                builder.backspace()
            elif key == ord("c"):
                builder.clear()
            elif key == ord("a"):
                builder.auto_commit = not builder.auto_commit
            elif key == ord("s"):
                if speaker is None:
                    from asl.tts import Speaker
                    speaker = Speaker()
                speaker.say(builder.text)
            elif key == ord("t"):
                typing, typed = True, ""
            elif key in (ord("1"), ord("2"), ord("3")):
                options = builder.suggestions()
                choice = key - ord("1")
                if choice < len(options):
                    builder.apply_suggestion(options[choice])
    finally:
        detector.close()
        cap.release()
        if speaker:
            speaker.close()
        if not headless:
            cv2.destroyAllWindows()
    return builder.text


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", default=str(config.CAMERA_INDEX), help="camera index or video file")
    p.add_argument("--model", type=Path, default=config.MODEL_PATH)
    p.add_argument("--mode", choices=[LETTER, PHRASE], default=LETTER, type=str.upper)
    p.add_argument("--headless", action="store_true", help="no window; print what gets added")
    p.add_argument("--data-dir", type=Path, default=config.DATA_DIR, help="images for the text-to-sign viewer")
    a = p.parse_args(argv)
    text = run(a.source, a.model, a.headless, a.mode, a.data_dir)
    print(f"\nFinal text: {text!r}")


if __name__ == "__main__":
    main()
