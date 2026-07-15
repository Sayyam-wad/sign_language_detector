import os
import pickle
import mediapipe as mp
import cv2
import numpy as np
from mapping import COMPLETE_MAPPING


def calculate_distance_features(hand_landmarks):
    """
    Calculates 42 key Euclidean distances between landmarks for a robust feature vector.
    
    Feature breakdown:
    - 20 features: Distances from wrist (landmark 0) to all other landmarks
    - 10 features: Distances between all fingertips (5 choose 2)
    - 6 features: Distances between metacarpals/knuckles (4 choose 2)
    - 6 features: Key cross-finger/palm distances
    Total: 42 features
    """
    feature_vector = []
    
    # 1. Distances from the Wrist (Landmark 0) to all other 20 landmarks (20 features)
    wrist_lm = hand_landmarks.landmark[0]
    for i in range(1, 21):
        lm = hand_landmarks.landmark[i]
        distance = np.sqrt((lm.x - wrist_lm.x)**2 + (lm.y - wrist_lm.y)**2)
        feature_vector.append(distance) 

    # 2. Distances between adjacent Fingertips (5 choose 2 = 10 features)
    # Indices: 4 (Thumb), 8 (Index), 12 (Middle), 16 (Ring), 20 (Pinky)
    fingertip_indices = [4, 8, 12, 16, 20] 
    for i in range(len(fingertip_indices)):
        for j in range(i + 1, len(fingertip_indices)):
            lm1 = hand_landmarks.landmark[fingertip_indices[i]]
            lm2 = hand_landmarks.landmark[fingertip_indices[j]]
            distance = np.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2)
            feature_vector.append(distance) 
            
    # 3. Distances between adjacent Metacarpals/Knuckles (4 choose 2 = 6 features)
    # Indices: 5 (Index Knuckle), 9 (Middle), 13 (Ring), 17 (Pinky)
    metacarpal_indices = [5, 9, 13, 17]
    for i in range(len(metacarpal_indices)):
        for j in range(i + 1, len(metacarpal_indices)):
            lm1 = hand_landmarks.landmark[metacarpal_indices[i]]
            lm2 = hand_landmarks.landmark[metacarpal_indices[j]]
            distance = np.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2)
            feature_vector.append(distance) 

    # 4. Key Cross-Finger/Palm Distances (6 features to pad to 42)
    key_pairs = [(4, 5), (8, 9), (12, 13), (16, 17), (20, 17), (4, 17)]
    for i, j in key_pairs:
        lm1 = hand_landmarks.landmark[i]
        lm2 = hand_landmarks.landmark[j]
        distance = np.sqrt((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2)
        feature_vector.append(distance) 
        
    return feature_vector  # Total 42 features


# --- Setup MediaPipe ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.1)

# --- Define Data Directory (SHARED with asl/ folder) ---
DATA_DIR = 'E:/Projects/sign_language_working_project/data'
print("="*60)
print("ASL FINGERSPELLING DATASET CREATION")
print("="*60)
print(f"\n✨ Processing data from: {DATA_DIR}")
print(f"📦 This includes your existing 18 classes (A-R) + new classes (S-Z)\n")

data = []
labels = []
samples_processed = 0
samples_detected = 0

# Use the complete mapping
labels_map = COMPLETE_MAPPING

# --- Data Collection Loop ---
if not os.path.isdir(DATA_DIR):
    print(f"🛑 ERROR: Data directory not found at {DATA_DIR}")
    print("Please run 'collect_imgs.py' first to collect images!")
else:
    for dir_ in sorted(os.listdir(DATA_DIR), key=lambda x: int(x) if x.isdigit() else 0):
        dir_path = os.path.join(DATA_DIR, dir_)
        
        if not os.path.isdir(dir_path):
            continue
        
        # Get letter name for display
        class_num = int(dir_)
        letter = labels_map.get(class_num, dir_)
        
        print(f"📦 Processing class {dir_} - Letter '{letter}'")
        
        for img_path in os.listdir(dir_path):
            full_path = os.path.join(dir_path, img_path)
            samples_processed += 1
            
            # data_aux list will hold the 42 distance features
            data_aux = []
            
            img = cv2.imread(full_path)
            
            if img is None:
                print(f"  ❌ Failed to read image: {img_path}")
                continue

            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(img_rgb)

            if results.multi_hand_landmarks:
                samples_detected += 1
                
                # Process ONLY the FIRST detected hand
                hand_landmarks = results.multi_hand_landmarks[0] 
                
                # Extract features using distance calculation
                data_aux = calculate_distance_features(hand_landmarks)

                # Append the consistent 42-element distance vector
                data.append(data_aux)
                labels.append(dir_)
                
            else:
                print(f"  ⚠️ No hand detected in: {img_path}")

# Clean up
cv2.destroyAllWindows() 

# --- Final Output and Pickle Save ---
print("\n" + "="*60)
print("DATASET CREATION SUMMARY")
print("="*60)
print(f"📝 Total images processed: {samples_processed}")
print(f"✅ Total hands detected: {samples_detected}")
print(f"💾 Total samples collected: {len(data)}")

if len(data) > 0:
    print(f"📊 Feature vector size: {len(data[0])} features per sample")
    print(f"📋 Unique classes: {len(set(labels))}")
    
    with open('data.pickle', 'wb') as f:
        pickle.dump({'data': data, 'labels': labels}, f)
    print("\n✅ Saved 'data.pickle' successfully!")
    print("\nNext step: Run 'train_classifier.py' to train the model")
else:
    print("\n⚠️ No data collected!")
    print("Please check your image quality and directory structure.")
    print("Run 'collect_imgs.py' first to collect training images.")
