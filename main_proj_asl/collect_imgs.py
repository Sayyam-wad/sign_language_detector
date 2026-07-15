import os
import cv2
import time
from mapping import COMPLETE_MAPPING, MISSING_CLASSES, SIGNS_TO_COLLECT, CLASSES_TO_COLLECT
from config import CAMERA_INDEX, DATA_DIR


# Use the shared data directory from config
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Only collect missing classes (C-K, M-Z: classes 18-40)
dataset_size = 100

# Full mapping for reference
labels_map = COMPLETE_MAPPING

# Classes that need to be collected (missing alphabet letters)
classes_to_collect = CLASSES_TO_COLLECT
signs_to_collect = SIGNS_TO_COLLECT

# Initialize camera with error handling
print("\n🔄 Initializing camera...")
print(f"   Attempting to open camera index: {CAMERA_INDEX}")

cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)  # Use DirectShow for Windows
if not cap.isOpened():
    print(f"\n❌ ERROR: Cannot open camera at index {CAMERA_INDEX}")
    print("\n🔧 TROUBLESHOOTING:")
    print("   1. Make sure your phone camera app (DroidCam/IP Webcam) is running")
    print("   2. Run 'python test_camera.py' to find the correct camera index")
    print(f"   3. Update CAMERA_INDEX in config.py (currently set to {CAMERA_INDEX})")
    print("   4. If using phone camera, ensure it's connected via USB or same WiFi network")
    exit(1)

# Set camera properties for better performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

# Test if we can actually read frames
print("   Testing camera connection...")
retry_count = 0
max_retries = 5
while retry_count < max_retries:
    ret, test_frame = cap.read()
    if ret and test_frame is not None and test_frame.size > 0:
        print("   ✅ Camera is working!\n")
        break
    retry_count += 1
    print(f"   Attempt {retry_count}/{max_retries}...")
    time.sleep(1)

if retry_count == max_retries:
    print(f"\n❌ ERROR: Camera opened but cannot read frames")
    print("\n🔧 TROUBLESHOOTING:")
    print("   1. The camera might be in use by another application")
    print("   2. Try closing other apps that might be using the camera")
    print("   3. Restart your phone camera app")
    print("   4. Try a different camera index in config.py")
    cap.release()
    exit(1)

print("="*60)
print("ASL FINGERSPELLING + PHRASES DATA COLLECTION")
print("="*60)
print(f"\n✅ Reusing existing data for classes 0-17:")
print(f"   Letters: A, B, L")
print(f"   Phrases: I Love You, YES, NO, OKAY, THANKYOU, RESTROOM, etc.")
print(f"\n📸 Collecting {dataset_size} images for {len(classes_to_collect)} missing classes")
print(f"Missing Letters: {', '.join(signs_to_collect)}")
print(f"\nData will be saved to: {DATA_DIR}\n")

for j in classes_to_collect:
    if not os.path.exists(os.path.join(DATA_DIR, str(j))):
        os.makedirs(os.path.join(DATA_DIR, str(j)))

    print(f'\n📸 Collecting data for class {j} - Letter "{labels_map[j]}"')
    print(f'   Make the sign for "{labels_map[j]}" with your hand')

    # Wait for user to be ready
    done = False
    while True:
        ret, frame = cap.read()
        
        # Check if frame is valid
        if not ret or frame is None or frame.size == 0:
            print(f"\n⚠️  Warning: Lost camera connection. Attempting to reconnect...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            continue
        
        frame = cv2.flip(frame, 1)  # Mirror the frame
        
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Display instructions - KEEP TEXT AT TOP AND BOTTOM EDGES ONLY
        # Top-left corner - Letter name
        cv2.putText(frame, f'Letter: {labels_map[j]}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        
        # Bottom area - Instructions (keep clear of hand in center)
        cv2.putText(frame, 'Ready? Press "Q" to start!', (10, height - 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Class {classes_to_collect.index(j)+1}/{len(classes_to_collect)}', (10, height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        cv2.imshow('Collect Images', frame)
        if cv2.waitKey(25) == ord('q'):
            break

    # Collect images
    counter = 0
    print(f'   Collecting images...')
    print(f'   📹 Text overlay REMOVED - saving clean images!')
    while counter < dataset_size:
        ret, frame = cap.read()
        
        # Check if frame is valid
        if not ret or frame is None or frame.size == 0:
            print(f"\n⚠️  Warning: Lost camera connection. Attempting to reconnect...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            continue
        
        frame = cv2.flip(frame, 1)  # Mirror the frame
        
        # Save the CLEAN frame without any text overlay
        clean_frame = frame.copy()
        
        # Get frame dimensions for display text only
        height, width = frame.shape[:2]
        
        # Add text ONLY for display (not saved to file)
        # Top-left corner - Letter and count
        cv2.putText(frame, f'Letter: {labels_map[j]}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Collecting: {counter}/{dataset_size}', (10, 65), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Bottom area - Instructions (keep clear of hand in center)
        cv2.putText(frame, 'Hold the sign steady!', (10, height - 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, 'Press ESC to stop collection', (10, height - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)
        
        # Show frame WITH text for user feedback
        cv2.imshow('Collect Images', frame)
        key = cv2.waitKey(25)
        
        # Allow early exit with ESC key
        if key == 27:  # ESC key
            print(f'\n   ⚠️  Collection stopped early by user at {counter}/{dataset_size} images')
            break
        
        # Save the CLEAN frame WITHOUT text overlay
        cv2.imwrite(os.path.join(DATA_DIR, str(j), '{}.jpg'.format(counter)), clean_frame)
        counter += 1
    
    print(f'   ✅ Completed {labels_map[j]} ({dataset_size} images)')

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print("✅ DATA COLLECTION COMPLETED!")
print("="*60)
print(f"Total NEW images collected: {len(classes_to_collect) * dataset_size}")
print(f"Total images in dataset: {41 * dataset_size} (including existing classes)")
print(f"   - 18 existing classes (3 letters + 15 phrases)")
print(f"   - 23 new letter classes (C-K, M-Z)")
print(f"Next step: Run 'create_dataset.py' to process ALL images (including existing)")
