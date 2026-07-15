"""
Script to delete collected images that have text overlays
Use this to clean up before recollecting with fixed text positioning

⚠️  SAFETY: This will ONLY delete classes you just collected (missing letters)
✅ SAFE: Your existing 18 classes (0-17: A, B, L + phrases) will NOT be touched
"""
import os
import shutil
from mapping import CLASSES_TO_COLLECT, EXISTING_CLASSES, MISSING_CLASSES
from config import DATA_DIR

print("="*60)
print("CLEANUP SCRIPT - Delete Images with Text Overlays")
print("="*60)

# Double safety check: Only delete classes that are in MISSING_CLASSES
# This excludes your existing 18 classes (0-17)
classes_to_delete = CLASSES_TO_COLLECT

print(f"\n🛡️  SAFETY CHECK:")
print(f"   ✅ Your existing classes (0-17) are PROTECTED")
print(f"   ✅ Only newly collected missing letters will be deleted")
print(f"\n⚠️  This will DELETE images for {len(classes_to_delete)} classes:")
print(f"   Classes to delete: {classes_to_delete}")
print(f"   Letters: {', '.join([MISSING_CLASSES[c] for c in classes_to_delete])}")
print(f"\n📁 Directory: {DATA_DIR}")

# Show existing classes that will NOT be touched
print(f"\n🔒 PROTECTED - Will NOT delete these classes:")
for class_id in sorted(EXISTING_CLASSES.keys()):
    folder_path = os.path.join(DATA_DIR, str(class_id))
    if os.path.exists(folder_path):
        image_count = len([f for f in os.listdir(folder_path) if f.endswith('.jpg')])
        print(f"   ✅ Class {class_id} ({EXISTING_CLASSES[class_id]}): {image_count} images - SAFE")


# Show which folders will be deleted
print(f"\n🗑️  WILL DELETE - These newly collected classes:")
folders_to_delete = []
for class_id in classes_to_delete:
    folder_path = os.path.join(DATA_DIR, str(class_id))
    if os.path.exists(folder_path):
        image_count = len([f for f in os.listdir(folder_path) if f.endswith('.jpg')])
        folders_to_delete.append((folder_path, image_count))
        print(f"   ❌ Class {class_id} ({MISSING_CLASSES[class_id]}): {image_count} images - WILL DELETE")


if not folders_to_delete:
    print("\n✅ No images found to delete. You're good to go!")
    exit(0)

total_images = sum(count for _, count in folders_to_delete)
print(f"\n📊 Total images to delete: {total_images}")

# Ask for confirmation
print("\n" + "="*60)
response = input("❓ Type 'yes' to DELETE these images and start fresh: ").strip().lower()

if response == 'yes':
    print("\n🗑️  Deleting folders...")
    deleted_count = 0
    for folder_path, image_count in folders_to_delete:
        try:
            # Extract class number from folder path for final safety check
            class_num = int(os.path.basename(folder_path))
            
            # FINAL SAFETY CHECK: Never delete classes 0-17 (existing data)
            if class_num in EXISTING_CLASSES.keys():
                print(f"   🛡️  BLOCKED: {folder_path} - This is protected existing data!")
                continue
            
            # Safe to delete - this is a newly collected class
            shutil.rmtree(folder_path)
            deleted_count += 1
            print(f"   ✅ Deleted: {folder_path} ({image_count} images)")
        except Exception as e:
            print(f"   ❌ Error deleting {folder_path}: {e}")
    
    print(f"\n✅ Done! Deleted {deleted_count} folders with {total_images} images")
    print("\n📸 Now you can run 'python collect_imgs.py' to recollect with fixed text positioning!")
else:
    print("\n❌ Cancelled. No images were deleted.")
    print("   If you want to keep these images, they may affect model accuracy.")
