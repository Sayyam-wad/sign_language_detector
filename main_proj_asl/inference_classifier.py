import pickle
import cv2
import pyttsx3
import mediapipe as mp
import numpy as np
import time
import os
from collections import deque, Counter
from mapping import COMPLETE_MAPPING, AMBIGUOUS_GESTURES, AMBIGUOUS_CLASS_NUMBERS, SIGN_TO_CLASS
from config import CAMERA_INDEX, DATA_DIR


# ---------------- TEXT-TO-SPEECH SETUP ---------------- #
def speak_text(text: str):
    """Speak the given text using pyttsx3."""
    try:
        # Initialize engine fresh each time to avoid issues
        engine = pyttsx3.init()
        engine.setProperty('rate', 120)    # Slower speed of speech
        engine.setProperty('volume', 1.0)  # Max volume
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        del engine  # Clean up
    except Exception as e:
        print(f"❌ Speech error: {e}")
        print(f"   Attempted to speak: {text}")


# --- FEATURE CALCULATION FUNCTION (Euclidean Distances) --- #
def calculate_distance_features_inference(hand_landmarks, is_right_hand):
    """
    Calculates 42 key Euclidean distances after applying X-coordinate
    flipping for right hands to maintain training consistency.
    """

    # 1. Pre-process landmarks (flip X for right hand)
    processed_landmarks = []

    class LandmarkCopy:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z

    for landmark in hand_landmarks.landmark:
        # Copy coordinates and flip X if right hand
        x_coord = landmark.x
        if is_right_hand:
            x_coord = 1.0 - landmark.x  # Mirror horizontally

        lm_copy = LandmarkCopy(x_coord, landmark.y, landmark.z)
        processed_landmarks.append(lm_copy)

    feature_vector = []

    # 2. Calculate distances (42 features total)

    # Distances from the Wrist (Landmark 0) (20 features)
    wrist_lm = processed_landmarks[0]
    for i in range(1, 21):
        lm = processed_landmarks[i]
        distance = np.sqrt((lm.x - wrist_lm.x) ** 2 + (lm.y - wrist_lm.y) ** 2)
        feature_vector.append(distance)

    # Distances between Fingertips (10 features)
    fingertip_indices = [4, 8, 12, 16, 20]
    for i in range(len(fingertip_indices)):
        for j in range(i + 1, len(fingertip_indices)):
            lm1 = processed_landmarks[fingertip_indices[i]]
            lm2 = processed_landmarks[fingertip_indices[j]]
            distance = np.sqrt((lm1.x - lm2.x) ** 2 + (lm1.y - lm2.y) ** 2)
            feature_vector.append(distance)

    # Distances between Metacarpals/Knuckles (6 features)
    metacarpal_indices = [5, 9, 13, 17]
    for i in range(len(metacarpal_indices)):
        for j in range(i + 1, len(metacarpal_indices)):
            lm1 = processed_landmarks[metacarpal_indices[i]]
            lm2 = processed_landmarks[metacarpal_indices[j]]
            distance = np.sqrt((lm1.x - lm2.x) ** 2 + (lm1.y - lm2.y) ** 2)
            feature_vector.append(distance)

    # Key Cross-Finger/Palm Distances (6 features)
    key_pairs = [(4, 5), (8, 9), (12, 13), (16, 17), (20, 17), (4, 17)]
    for i, j in key_pairs:
        lm1 = processed_landmarks[i]
        lm2 = processed_landmarks[j]
        distance = np.sqrt((lm1.x - lm2.x) ** 2 + (lm1.y - lm2.y) ** 2)
        feature_vector.append(distance)

    return feature_vector


# ---------------- LOAD MODEL AND SETUP ---------------- #
print("="*60)
print("ASL FINGERSPELLING REAL-TIME RECOGNITION")
print("="*60)

try:
    model_dict = pickle.load(open('./model.p', 'rb'))
    model = model_dict['model']
    scaler = model_dict['scaler']
    labels_map = model_dict['labels_map']
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print("🛑 ERROR: model.p not found!")
    print("Please run 'train_classifier.py' first to train the model.")
    exit()
except Exception as e:
    print(f"🛑 ERROR loading model: {e}")
    exit()

# Reverse the labels_map for easy lookup
reverse_labels_map = {v: k for k, v in labels_map.items()}

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ---------------- MAIN INFERENCE LOOP ---------------- #
# Use camera index from config (0 = internal, 1+ = external/phone camera)
cap = cv2.VideoCapture(CAMERA_INDEX)

# Variables for word building and timing
predicted_letters = deque(maxlen=10)  # Rolling buffer for stable predictions
current_word = ""
current_letter = ""  # The letter currently being shown (not yet confirmed)
last_confirmed_letter = ""  # Last letter that was added to the word

# MODE TOGGLE VARIABLES
recognition_mode = "PHRASE"  # Can be "LETTER" or "PHRASE"
text_to_sign_mode = False  # Toggle for text-to-sign display mode
input_text = ""  # Text input for reverse mode
mode_colors = {
    "LETTER": (0, 255, 255),   # Yellow for letter mode
    "PHRASE": (255, 0, 255)     # Magenta for phrase mode
}

def get_sign_image(character_or_phrase):
    """Get a sample image for the given character or phrase"""
    char = character_or_phrase.upper().strip()
    
    if char not in SIGN_TO_CLASS:
        return None
    
    class_num = SIGN_TO_CLASS[char]
    folder_path = os.path.join(DATA_DIR, str(class_num))
    
    if not os.path.exists(folder_path):
        return None
    
    images = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
    if not images:
        return None
    
    img_path = os.path.join(folder_path, images[0])
    return cv2.imread(img_path)

print("\n📹 Starting webcam...")
print("\n🎮 Controls:")
print("  - Press 'L' to switch to LETTER mode (fingerspelling)")
print("  - Press 'P' to switch to PHRASE mode (gestures/words)")
print("  - Press 'ENTER' to confirm the detected letter and add to word")
print("  - Press 'SPACEBAR' to add a space")
print("  - Press '5' to toggle TEXT-TO-SIGN mode (type text, see signs)")
print("  - Press 'C' to clear the current word")
print("  - Press 'S' to speak the current word")
print("  - Press 'Q' to quit")
print("\n" + "="*60)
print(f"🔹 Starting in: {recognition_mode} MODE")
print("="*60 + "\n")

no_hand_start_time = None

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to grab frame")
        break
    
    frame = cv2.flip(frame, 1)  # Mirror the frame
    H, W, _ = frame.shape
    
    # TEXT-TO-SIGN MODE: Show sign images for typed text
    if text_to_sign_mode:
        # Create a display frame
        display_frame = np.zeros((H, W, 3), dtype=np.uint8)
        
        # Display input text
        cv2.putText(display_frame, 'TEXT-TO-SIGN MODE', (10, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(display_frame, f'Text: {input_text}_', (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2, cv2.LINE_AA)
        
        # Show signs for the text
        if input_text:
            tokens = input_text.upper().split()
            sign_images = []
            sign_labels = []
            
            for token in tokens:
                # Check if entire token is a phrase
                if token in SIGN_TO_CLASS:
                    img = get_sign_image(token)
                    if img is not None:
                        sign_images.append(img)
                        sign_labels.append(token)
                else:
                    # Process letter by letter
                    for char in token:
                        if char.strip():
                            img = get_sign_image(char)
                            if img is not None:
                                sign_images.append(img)
                                sign_labels.append(char)
            
            # Display sign images in a row
            if sign_images:
                y_offset = 140
                x_offset = 10
                max_display = 5  # Show max 5 signs at once
                
                for i, (img, label) in enumerate(zip(sign_images[-max_display:], sign_labels[-max_display:])):
                    # Resize image
                    img_resized = cv2.resize(img, (150, 150))
                    
                    # Add label
                    cv2.putText(img_resized, label, (5, 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
                    
                    # Place on display frame
                    if x_offset + 150 <= W:
                        display_frame[y_offset:y_offset+150, x_offset:x_offset+150] = img_resized
                        x_offset += 160
        
        # Instructions
        cv2.putText(display_frame, 'Type text (A-Z, phrases)', (10, H - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(display_frame, 'T: Exit mode | BACKSPACE: Delete | SPACE: Space', (10, H - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
        cv2.imshow('ASL Recognition - Letter + Phrase Mode', display_frame)
        
        # Handle keyboard input for text-to-sign mode
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('t'):
            text_to_sign_mode = False
            input_text = ""
            print("\n🔙 Exited TEXT-TO-SIGN mode")
        elif key == ord('q'):
            break
        elif key == 8:  # BACKSPACE
            input_text = input_text[:-1]
        elif key == 32:  # SPACE
            input_text += ' '
        elif 32 < key < 127:  # Printable characters
            input_text += chr(key)
        
        continue
    
    # NORMAL MODE: Hand recognition
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process frame with MediaPipe
    results = hands.process(frame_rgb)
    
    predicted_character = ""
    confidence = 0
    
    if results.multi_hand_landmarks:
        no_hand_start_time = None  # Reset no-hand timer
        
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Draw hand landmarks
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            
            # Determine hand type (left/right)
            hand_label = results.multi_handedness[hand_idx].classification[0].label
            is_right_hand = (hand_label == "Right")
            
            # Calculate features
            data_aux = calculate_distance_features_inference(hand_landmarks, is_right_hand)
            
            # Scale features
            data_aux_scaled = scaler.transform([np.asarray(data_aux)])
            
            # Predict
            prediction = model.predict(data_aux_scaled)
            predicted_class = int(prediction[0])
            predicted_class_str = str(predicted_class)
            
            # MODE-AWARE INTERPRETATION
            # Check if this is an ambiguous gesture
            if predicted_class in AMBIGUOUS_CLASS_NUMBERS:
                # This gesture has dual meaning - use current mode
                ambiguous_info = AMBIGUOUS_GESTURES[predicted_class]
                if recognition_mode == "LETTER":
                    predicted_character = ambiguous_info['letter']
                else:  # PHRASE mode
                    predicted_character = ambiguous_info['phrase']
            else:
                # Unambiguous gesture - use the label directly
                predicted_character = labels_map.get(predicted_class_str, predicted_class_str)
            
            # Get confidence if available
            if hasattr(model, 'predict_proba'):
                confidence = np.max(model.predict_proba(data_aux_scaled))
            
            # Add to rolling buffer
            predicted_letters.append(predicted_character)
            
            # Get most common prediction from buffer
            if len(predicted_letters) > 0:
                most_common = Counter(predicted_letters).most_common(1)[0]
                stable_prediction = most_common[0]
                
                # Update current letter being shown (not yet confirmed)
                current_letter = stable_prediction
            
            # Draw bounding box
            x_coords = [landmark.x for landmark in hand_landmarks.landmark]
            y_coords = [landmark.y for landmark in hand_landmarks.landmark]
            
            x1 = int(min(x_coords) * W) - 10
            y1 = int(min(y_coords) * H) - 10
            x2 = int(max(x_coords) * W) + 10
            y2 = int(max(y_coords) * H) + 10
            
            # Draw rectangle and prediction
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'{predicted_character} ({confidence:.2f})', 
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                       1.0, (0, 255, 0), 2, cv2.LINE_AA)
    else:
        # No hand detected - reset current letter
        current_letter = ""
    
    # Display current letter being detected (not yet added to word)
    if current_letter:
        cv2.putText(frame, f'Detected: {current_letter}', (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, '(Press ENTER to add)', (10, 190), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
    
    # Display current word - with text wrapping if too long
    max_word_length = 40  # Maximum characters per line
    if len(current_word) > max_word_length:
        # Split into multiple lines
        words_display = current_word[-max_word_length:]  # Show last 40 chars
        cv2.putText(frame, f'Word: ...{words_display}', (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2, cv2.LINE_AA)
    else:
        cv2.putText(frame, f'Word: {current_word}', (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2, cv2.LINE_AA)
    
    # Display current mode (with color coding)
    mode_color = mode_colors[recognition_mode]
    cv2.putText(frame, f'Mode: {recognition_mode}', (10, 100), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, mode_color, 2, cv2.LINE_AA)
    
    # Display instructions
    cv2.putText(frame, 'ENTER: Add | SPACE: Space | 5: Text-to-Sign | C: Clear | S: Speak | Q: Quit', (10, H - 20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    
    cv2.imshow('ASL Recognition - Letter + Phrase Mode', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        print("\nExiting...")
        break
    elif key == ord('5'):
        text_to_sign_mode = True
        input_text = ""
        print("\n🔤 Entered TEXT-TO-SIGN mode")
        print("   Type text and see the corresponding signs!")
    elif key == 13:  # ENTER key
        if current_letter and current_letter != last_confirmed_letter:
            current_word += current_letter
            last_confirmed_letter = current_letter
            print(f"✅ Added '{current_letter}' to word: {current_word}")
            predicted_letters.clear()  # Clear buffer after adding
    elif key == 32:  # SPACEBAR
        if current_word and not current_word.endswith(' '):
            current_word += ' '
            print(f"Added space to word: '{current_word}'")
    elif key == ord('c'):
        current_word = ""
        current_letter = ""
        last_confirmed_letter = ""
        predicted_letters.clear()
        print("Cleared word")
    elif key == ord('s'):
        if current_word:
            print(f"Speaking: {current_word}")
            speak_text(current_word)
    elif key == ord('l'):
        recognition_mode = "LETTER"
        predicted_letters.clear()  # Clear buffer when switching modes
        print("\n🔤 Switched to LETTER mode (fingerspelling)")
        print("   Ambiguous gestures will be interpreted as letters")
    elif key == ord('p'):
        recognition_mode = "PHRASE"
        predicted_letters.clear()  # Clear buffer when switching modes
        print("\n💬 Switched to PHRASE mode (gestures/words)")
        print("   Ambiguous gestures will be interpreted as phrases")

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print("✅ Program terminated successfully")
print("="*60)
