"""
Recollect specific classes that are being confused
Use this to improve specific letter recognition
"""
import os
import cv2
import time
from mapping import COMPLETE_MAPPING
from config import CAMERA_INDEX, DATA_DIR
import shutil

# Classes to recollect
CLASSES_TO_RECOLLECT = {
    18: 'C',
    29: 'O'
}

dataset_size = 100

print("="*60)
print("RECOLLECT SPECIFIC LETTERS")
print("="*60)
print("\n📝 This will help fix confusion between similar letters")
print("\nLetters to recollect:")
for class_id, letter in CLASSES_TO_RECOLLECT.items():
    print(f"  - Class {class_id}: Letter '{letter}'")

print(f"\n⚠️  TIPS for better distinction:")
print("  📌 Letter C: Make it tighter/more curved than NO gesture")
print("  📌 Letter O: Perfect circle with thumb+index, tighter than OKAY")
print("  📌 Vary hand positions, angles, and distances from camera")
print("  📌 Good lighting helps!")

response = input("\nDelete old images and recollect? (yes/no): ").strip().lower()
if response != 'yes':
    print("Cancelled.")
    exit()

# Delete old folders
for class_id in CLASSES_TO_RECOLLECT.keys():
    folder_path = os.path.join(DATA_DIR, str(class_id))
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"🗑️  Deleted old images for class {class_id}")

# Initialize camera
print("\n🔄 Initializing camera...")
cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    print(f"❌ Cannot open camera at index {CAMERA_INDEX}")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Test camera
retry = 0
while retry < 5:
    ret, test_frame = cap.read()
    if ret and test_frame is not None and test_frame.size > 0:
        break
    retry += 1
    time.sleep(1)

if retry == 5:
    print("❌ Camera test failed")
    cap.release()
    exit(1)

print("✅ Camera ready!\n")

# Collect images
for class_id, letter in CLASSES_TO_RECOLLECT.items():
    folder_path = os.path.join(DATA_DIR, str(class_id))
    os.makedirs(folder_path, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"📸 Collecting Letter '{letter}' (Class {class_id})")
    print(f"{'='*60}")
    
    if letter == 'C':
        print("💡 TIP: Make it TIGHTER and MORE CURVED than NO gesture")
    elif letter == 'O':
        print("💡 TIP: Perfect CIRCLE with thumb+index, tighter than OKAY")
    
    # Preview mode
    while True:
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            continue
        
        frame = cv2.flip(frame, 1)
        height, width = frame.shape[:2]
        
        # Top text
        cv2.putText(frame, f'Letter: {letter}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        
        # Bottom instructions
        cv2.putText(frame, 'Ready? Press Q to start!', (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_AA)
        
        cv2.imshow('Recollect Letters', frame)
        if cv2.waitKey(25) == ord('q'):
            break
    
    # Collection mode
    counter = 0
    print(f"   Collecting {dataset_size} images...")
    while counter < dataset_size:
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            continue
        
        frame = cv2.flip(frame, 1)
        clean_frame = frame.copy()  # Save without text
        
        height, width = frame.shape[:2]
        
        # Add text for display only
        cv2.putText(frame, f'Letter: {letter}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f'Collecting: {counter}/{dataset_size}', (10, 65), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, 'Hold steady! ESC to skip', (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        cv2.imshow('Recollect Letters', frame)
        key = cv2.waitKey(25)
        
        if key == 27:  # ESC
            print(f"   ⚠️  Skipped at {counter}/{dataset_size}")
            break
        
        # Save clean frame
        cv2.imwrite(os.path.join(folder_path, f'{counter}.jpg'), clean_frame)
        counter += 1
    
    print(f"   ✅ Completed: {counter} images")

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print("✅ Recollection complete!")
print("="*60)
print("\n📋 Next steps:")
print("  1. Run: python create_dataset.py")
print("  2. Run: python train_classifier.py")
print("  3. Test: python inference_classifier.py")
print("\n   The model should now better distinguish C from O!")
