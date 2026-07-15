"""
System Check Script for ASL Fingerspelling Recognition
Run this script to verify all dependencies are properly installed
"""

import sys

print("="*60)
print("ASL FINGERSPELLING - SYSTEM CHECK")
print("="*60)
print()

# Track success
all_good = True

# Check Python version
print("1. Checking Python version...")
if sys.version_info >= (3, 7):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"   ❌ Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.7+)")
    all_good = False

# Check OpenCV
print("\n2. Checking OpenCV...")
try:
    import cv2
    print(f"   ✅ OpenCV {cv2.__version__}")
except ImportError:
    print("   ❌ OpenCV not found")
    print("   Install with: pip install opencv-python")
    all_good = False

# Check MediaPipe
print("\n3. Checking MediaPipe...")
try:
    import mediapipe as mp
    print(f"   ✅ MediaPipe {mp.__version__}")
except ImportError:
    print("   ❌ MediaPipe not found")
    print("   Install with: pip install mediapipe")
    all_good = False

# Check NumPy
print("\n4. Checking NumPy...")
try:
    import numpy as np
    print(f"   ✅ NumPy {np.__version__}")
except ImportError:
    print("   ❌ NumPy not found")
    print("   Install with: pip install numpy")
    all_good = False

# Check scikit-learn
print("\n5. Checking scikit-learn...")
try:
    import sklearn
    print(f"   ✅ scikit-learn {sklearn.__version__}")
except ImportError:
    print("   ❌ scikit-learn not found")
    print("   Install with: pip install scikit-learn")
    all_good = False

# Check pyttsx3
print("\n6. Checking pyttsx3 (Text-to-Speech)...")
try:
    import pyttsx3
    print(f"   ✅ pyttsx3")
    # Try to initialize engine
    try:
        engine = pyttsx3.init()
        print("   ✅ TTS engine initialized successfully")
    except Exception as e:
        print(f"   ⚠️  TTS engine warning: {e}")
        print("   Speech may not work, but recognition will still function")
except ImportError:
    print("   ❌ pyttsx3 not found")
    print("   Install with: pip install pyttsx3")
    all_good = False

# Check webcam
print("\n7. Checking webcam access...")
try:
    import cv2
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        print("   ✅ Webcam accessible")
        print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("   ⚠️  Webcam not accessible")
        print("   Please ensure no other application is using the camera")
    cap.release()
except Exception as e:
    print(f"   ❌ Webcam error: {e}")
    all_good = False

# Check write permissions
print("\n8. Checking file system permissions...")
try:
    import os
    test_file = ".__test_write__"
    with open(test_file, 'w') as f:
        f.write("test")
    os.remove(test_file)
    print("   ✅ Write permissions OK")
except Exception as e:
    print(f"   ❌ Cannot write to current directory: {e}")
    all_good = False

# Final summary
print("\n" + "="*60)
if all_good:
    print("✅ ALL CHECKS PASSED!")
    print("="*60)
    print("\nYou're ready to start!")
    print("\nNext steps:")
    print("  1. Run: python collect_imgs.py")
    print("  2. Run: python create_dataset.py")
    print("  3. Run: python train_classifier.py")
    print("  4. Run: python inference_classifier.py")
else:
    print("❌ SOME CHECKS FAILED")
    print("="*60)
    print("\nPlease install missing dependencies:")
    print("  pip install -r requirements.txt")
    print("\nOr install individually:")
    print("  pip install opencv-python mediapipe numpy scikit-learn pyttsx3")

print()
