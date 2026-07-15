"""
Configuration file for ASL Recognition System (Letters + Phrases)
Adjust these parameters to customize the behavior

NOTE: This configuration is set up to REUSE existing data from the asl/ folder!
- Classes 0-17: Already exist (3 letters: A, B, L + 15 phrases)
- Classes 18-40: Need to be collected (23 missing alphabet letters)
"""

# ==================== DATA COLLECTION SETTINGS ====================

# Number of classes (signs) to collect
# Default: 23 (C-K, M-Z only, since A, B, L already exist)
# Set to 41 if you want to recollect everything
NUM_CLASSES = 23  # Only missing letters

# Number of images to collect per class
# Increase for better accuracy, but takes longer to collect
# Recommended: 100-200
DATASET_SIZE = 100

# Data directory path (SHARED with asl/ folder)
# This reuses your existing data!
DATA_DIR = 'E:/Projects/sign_language_working_project/data'


# ==================== FEATURE EXTRACTION SETTINGS ====================

# MediaPipe hand detection confidence
# Range: 0.0 to 1.0
# Lower values detect more hands but may have false positives
MIN_DETECTION_CONFIDENCE = 0.1

# Whether to use static image mode
# False for video/webcam, True for static images
STATIC_IMAGE_MODE = False


# ==================== TRAINING SETTINGS ====================

# Train/test split ratio
# 0.8 means 80% training, 20% testing
TEST_SIZE = 0.2

# Random state for reproducibility
RANDOM_STATE = 42

# Model configurations
MODELS_CONFIG = {
    'random_forest_default': {
        'n_estimators': 100,
        'random_state': 42,
        'n_jobs': -1
    },
    'random_forest_optimized': {
        'n_estimators': 200,
        'max_depth': 20,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42,
        'n_jobs': -1
    },
    'svm': {
        'kernel': 'rbf',
        'C': 10,
        'gamma': 'scale',
        'random_state': 42,
        'probability': True
    }
}


# ==================== INFERENCE SETTINGS ====================

# Maximum number of hands to detect
# Set to 1 for fingerspelling (single hand)
MAX_NUM_HANDS = 1

# MediaPipe confidence thresholds for real-time detection
INFERENCE_MIN_DETECTION_CONFIDENCE = 0.5
INFERENCE_MIN_TRACKING_CONFIDENCE = 0.5

# Time (in seconds) to hold a sign before adding it to the word
# Increase if letters are being added too quickly
# Decrease for faster recognition (but less stable)
LETTER_HOLD_TIME = 1.5

# Time (in seconds) without hand detection to add a space
# Increase if spaces are being added too quickly
SPACE_TIME = 2.0

# Size of rolling prediction buffer
# Larger buffer = more stable but slower response
# Smaller buffer = faster but less stable
PREDICTION_BUFFER_SIZE = 10

# Camera device index
# 0 for default camera, 1 for external camera, etc.
CAMERA_INDEX = 0

# Mirror the camera feed
# True for mirrored view (easier for user)
# False for non-mirrored view
MIRROR_CAMERA = True


# ==================== TEXT-TO-SPEECH SETTINGS ====================

# Speech rate (words per minute)
# Range: 100-200 for natural speech
SPEECH_RATE = 150

# Speech volume
# Range: 0.0 (silent) to 1.0 (maximum)
SPEECH_VOLUME = 1.0


# ==================== DISPLAY SETTINGS ====================

# Colors (BGR format for OpenCV)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_WHITE = (255, 255, 255)

# Font settings
FONT = 1  # cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1.0
FONT_THICKNESS = 2


# ==================== FILE PATHS ====================

# Model save path
MODEL_PATH = './model.p'

# Dataset pickle path
DATASET_PICKLE_PATH = './data.pickle'


# ==================== ALPHABET MAPPING ====================

# Complete mapping from class index to sign (Letters A-Z + Phrases)
# Classes 0-17: Existing data from asl/ folder
# Classes 18-40: New alphabet letters to be collected
LABELS_MAP = {
    # Existing classes (0-17) - 3 letters + 15 phrases
    0: 'A', 1: 'B', 2: 'L',
    3: 'I Love You', 4: 'YES', 5: 'NO', 6: 'OKAY', 7: 'THANKYOU',
    8: 'RESTROOM', 9: 'INFINITE VOID', 10: 'HELLO', 11: 'PEACE',
    12: 'GOOD', 13: 'BAD', 14: 'TAKE CARE', 15: 'HOPE',
    16: 'I HATE YOU', 17: 'BYE',
    # New classes (18-40) - Missing alphabet letters
    18: 'C', 19: 'D', 20: 'E', 21: 'F', 22: 'G', 23: 'H', 24: 'I',
    25: 'J', 26: 'K', 27: 'M', 28: 'N', 29: 'O', 30: 'P', 31: 'Q',
    32: 'R', 33: 'S', 34: 'T', 35: 'U', 36: 'V', 37: 'W', 38: 'X',
    39: 'Y', 40: 'Z'
}

# Total number of classes
NUM_TOTAL_CLASSES = 41  # 18 existing + 23 new

# NOTE: Customize mapping in mapping.py file for detailed configuration!


# ==================== FEATURE ENGINEERING ====================

# Hand landmark indices for feature extraction
WRIST_INDEX = 0
FINGERTIP_INDICES = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
METACARPAL_INDICES = [5, 9, 13, 17]  # Knuckles
KEY_PAIRS = [(4, 5), (8, 9), (12, 13), (16, 17), (20, 17), (4, 17)]

# Expected number of features
NUM_FEATURES = 42


# ==================== ADVANCED SETTINGS ====================

# Enable debug mode (shows additional information)
DEBUG_MODE = False

# Save debug images during inference
SAVE_DEBUG_IMAGES = False
DEBUG_IMAGES_DIR = './debug_images'

# Enable performance metrics logging
LOG_PERFORMANCE = False

# Minimum confidence threshold for predictions
# Predictions below this confidence will be ignored
MIN_PREDICTION_CONFIDENCE = 0.0  # Set to 0.5-0.7 for more confident predictions only
