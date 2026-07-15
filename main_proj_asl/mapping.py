"""
ASL Mapping Configuration
Maps class numbers to ASL signs (letters and phrases)
"""

# Your existing 18 classes (0-17) from the asl/ folder
# These include both letters (A, B, L) and common phrases
EXISTING_CLASSES = {
    0: 'A',
    2: 'L',
    3: 'I Love You',
    4: 'YES',
    5: 'NO',
    6: 'OKAY',
    7: 'THANKYOU',
    8: 'RESTROOM',
    9: 'INFINITE VOID',
    10: 'HELLO',
    11: 'PEACE',
    12: 'GOOD',
    13: 'BAD',
    14: 'TAKE CARE',
    15: 'HOPE',
    16: 'I HATE YOU',
    17: 'BYE'
}

# Missing alphabet letters that need to be collected
# NOTE: Classes 0,5,7,9,11 already exist but with phrase names
# These will be handled by AMBIGUOUS_GESTURES in mode toggle
MISSING_CLASSES = {
    1: 'B',
    18: 'C',    # Also class 5 (NO) in phrase mode
    19: 'D',
    20: 'E',
    21: 'F',
    22: 'G',
    23: 'H',
    24: 'I',
    25: 'J',
    26: 'K',
    27: 'M',
    28: 'N',
    29: 'O',    # Also class 6 (OKAY) in phrase mode
    30: 'P',
    31: 'Q',
    32: 'R',    # Also class 9 (INFINITE VOID) in phrase mode
    33: 'S',    # Also class 0 (A) in phrase mode
    34: 'T',
    35: 'U',
    36: 'V',    # Also class 11 (PEACE) in phrase mode
    37: 'W',
    38: 'X',
    39: 'Y',    # Also class 7 (THANKYOU) in phrase mode
    40: 'Z'
}

# Complete mapping (Phrases + All Letters A-Z)
COMPLETE_MAPPING = {**EXISTING_CLASSES, **MISSING_CLASSES}

# Reverse mapping (sign to class number)
SIGN_TO_CLASS = {v: k for k, v in COMPLETE_MAPPING.items()}

# Separate alphabet letters and phrases
ALPHABET_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
PHRASES = [v for v in EXISTING_CLASSES.values() if v not in ALPHABET_LETTERS]

# List of signs that need to be collected
SIGNS_TO_COLLECT = list(MISSING_CLASSES.values())
CLASSES_TO_COLLECT = list(MISSING_CLASSES.keys())

# Ambiguous gestures that have dual meanings
# Format: {class_number: {'letter': 'X', 'phrase': 'PHRASE_NAME'}}
AMBIGUOUS_GESTURES = {
    0: {'letter': 'S', 'phrase': 'A'},            # Fist = S letter or A sign
    5: {'letter': 'C', 'phrase': 'NO'},           # C shape = NO gesture
    6: {'letter': 'O', 'phrase': 'OKAY'},         # O shape = OKAY gesture
    7: {'letter': 'Y', 'phrase': 'THANKYOU'},     # Y hand = THANKYOU gesture
    9: {'letter': 'R', 'phrase': 'INFINITE VOID'}, # R hand = INFINITE VOID gesture
    11: {'letter': 'V', 'phrase': 'PEACE'},       # V hand = PEACE sign
}

# Class numbers that are ambiguous
AMBIGUOUS_CLASS_NUMBERS = list(AMBIGUOUS_GESTURES.keys())

# Summary
TOTAL_CLASSES = len(COMPLETE_MAPPING)
EXISTING_COUNT = len(EXISTING_CLASSES)
MISSING_COUNT = len(MISSING_CLASSES)

if __name__ == "__main__":
    print("="*60)
    print("ASL MAPPING CONFIGURATION")
    print("="*60)
    print(f"\n✅ Existing classes ({EXISTING_COUNT}):")
    print(f"   Letters: A, L")
    print(f"   Phrases: {', '.join(PHRASES)}")
    print(f"\n📸 Missing letters to collect ({MISSING_COUNT}):")
    print(f"   {', '.join(SIGNS_TO_COLLECT)}")
    print(f"\n📊 Total classes: {TOTAL_CLASSES}")
    print(f"   - Existing: {EXISTING_COUNT}")
    print(f"   - To collect: {MISSING_COUNT}")
    print("\n" + "="*60)
