"""
Text to Sign Language Viewer
Type text and see the corresponding ASL signs from your dataset
"""
import os
import cv2
import numpy as np
from mapping import COMPLETE_MAPPING, SIGN_TO_CLASS
from config import DATA_DIR

print("="*60)
print("TEXT TO SIGN LANGUAGE VIEWER")
print("="*60)
print("\nType text and see the ASL signs from your collected images!")
print("This works for both letters (A-Z) and phrases.\n")

def get_sign_image(character_or_phrase):
    """Get a random image for the given character or phrase"""
    # Convert to uppercase for consistency
    char = character_or_phrase.upper().strip()
    
    # Check if this sign exists in our mapping
    if char not in SIGN_TO_CLASS:
        return None
    
    # Get the class number
    class_num = SIGN_TO_CLASS[char]
    
    # Get the folder path
    folder_path = os.path.join(DATA_DIR, str(class_num))
    
    if not os.path.exists(folder_path):
        return None
    
    # Get all images in this folder
    images = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
    
    if not images:
        return None
    
    # Pick the first image (or you can randomize)
    img_path = os.path.join(folder_path, images[0])
    img = cv2.imread(img_path)
    
    return img, char, class_num

def display_text_as_signs(text):
    """Display each character/word as sign language images"""
    print(f"\n📝 Text: {text}")
    print("="*60)
    
    # Split by spaces to handle phrases vs letters
    tokens = text.split()
    
    all_images = []
    labels = []
    
    for token in tokens:
        token_upper = token.upper().strip()
        
        # First check if entire token is a phrase
        if token_upper in SIGN_TO_CLASS:
            result = get_sign_image(token_upper)
            if result:
                img, char, class_num = result
                all_images.append(img)
                labels.append(f"{char} (Phrase)")
                print(f"  ✅ Found phrase: {char}")
                continue
        
        # Otherwise, process letter by letter
        for char in token_upper:
            if char == ' ':
                continue
                
            result = get_sign_image(char)
            if result:
                img, ch, class_num = result
                all_images.append(img)
                labels.append(f"{ch} (Letter)")
                print(f"  ✅ Found letter: {ch}")
            else:
                print(f"  ⚠️  No sign found for: {char}")
    
    if not all_images:
        print("\n❌ No signs found for this text!")
        return
    
    # Display images in a grid
    display_sign_grid(all_images, labels)

def display_sign_grid(images, labels):
    """Display multiple sign images in a grid"""
    num_images = len(images)
    
    if num_images == 0:
        return
    
    # Resize all images to same size
    target_size = (300, 300)
    resized = []
    for img in images:
        if img is not None:
            resized.append(cv2.resize(img, target_size))
    
    # Calculate grid dimensions
    cols = min(4, num_images)  # Max 4 columns
    rows = (num_images + cols - 1) // cols
    
    # Create grid
    grid_rows = []
    for r in range(rows):
        row_images = []
        for c in range(cols):
            idx = r * cols + c
            if idx < num_images:
                img = resized[idx].copy()
                # Add label
                cv2.putText(img, labels[idx], (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                row_images.append(img)
            else:
                # Empty placeholder
                row_images.append(np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8))
        
        grid_rows.append(np.hstack(row_images))
    
    final_grid = np.vstack(grid_rows)
    
    # Display
    cv2.imshow('Sign Language - Your Text', final_grid)
    print("\n✅ Displaying signs! Press any key to continue or Q to quit...")
    key = cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return key

# Main loop
while True:
    print("\n" + "="*60)
    text = input("📝 Enter text to convert to signs (or 'quit' to exit): ").strip()
    
    if text.lower() in ['quit', 'exit', 'q']:
        break
    
    if not text:
        continue
    
    key = display_text_as_signs(text)
    
    if key == ord('q'):
        break

print("\n✅ Program terminated")
print("="*60)
