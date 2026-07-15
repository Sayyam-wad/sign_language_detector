# ⌨️ Keyboard Controls Reference

## 📸 During Data Collection (collect_imgs.py)

### Ready Screen (Before collecting each letter):
| Key | Action |
|-----|--------|
| **Q** | Start collecting images for current letter |
| **X** (window close) | Close window and exit program |

### During Collection (While capturing 100 images):
| Key | Action |
|-----|--------|
| **ESC** | Stop collecting current letter early and move to next |
| **X** (window close) | Close window and exit program completely |

**Note:** Collection happens automatically once you press Q. Just hold the sign steady!

---

## 🎥 During Recognition (inference_classifier.py)

### Mode Controls:
| Key | Action |
|-----|--------|
| **L** | Switch to **Letter Mode** (fingerspelling) |
| **P** | Switch to **Phrase Mode** (gestures/phrases) |
| **M** | Switch to **Auto Mode** (automatic detection) |

### Word Building:
| Key | Action |
|-----|--------|
| **C** | **Clear** current word |
| **S** | **Speak** current word (text-to-speech) |

### Exit:
| Key | Action |
|-----|--------|
| **Q** | **Quit** the program |
| **ESC** | Alternative quit key |

### Automatic Actions:
| Action | Behavior |
|--------|----------|
| **Hold sign 1.5s** | Add letter/phrase to word |
| **Remove hand 2s** | Add space to word |

---

## 🎮 Quick Usage Guide

### Collecting Data:
```
1. Run: python collect_imgs.py
2. For each letter:
   - Position your hand
   - Press Q to start
   - Hold sign steady for ~1 minute
   - Press ESC if you want to skip/stop early
3. Repeat for all letters
```

### Using Recognition:
```
1. Run: python inference_classifier.py
2. Press L for letter mode (fingerspelling)
3. Press P for phrase mode (gestures)
4. Make signs with your hand
5. Press S to speak the word
6. Press C to clear and start over
7. Press Q to quit
```

---

## 💡 Pro Tips

### During Collection:
- **Don't press any keys** while collecting - it happens automatically!
- **Only press ESC** if you really want to stop early
- **Press Q** only at the "Ready?" screen

### During Recognition:
- **Letter Mode (L)**: Use for spelling words (H-E-L-L-O)
- **Phrase Mode (P)**: Use for quick phrases (YES, NO, HELLO)
- **Auto Mode (M)**: System decides based on context

### Current Mode Display:
The screen shows your current mode at the top:
```
┌────────────────────────────────┐
│ Mode: LETTER                   │  ← You're in letter mode
│ Word: HELLO                    │
│ C: Clear | S: Speak | Q: Quit │
└────────────────────────────────┘
```

---

## 🆘 Emergency Exit

If the program freezes or you need to force quit:
- **Windows**: Press `Ctrl + C` in the terminal
- **Or**: Close the terminal window
- **Or**: Press the X button on the camera window

---

## 📝 Summary Card

**Collection:**
- `Q` = Start collecting
- `ESC` = Stop/skip current letter

**Recognition:**
- `L` = Letter mode
- `P` = Phrase mode  
- `M` = Auto mode
- `C` = Clear word
- `S` = Speak word
- `Q` = Quit

---

**Remember: During collection, just hold the sign steady after pressing Q. The system captures automatically!**
