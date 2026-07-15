"""
DRY RUN - Shows what cleanup_images.py will delete WITHOUT actually deleting anything
Use this to verify your existing data (classes 0-17) is safe
"""
import os
from mapping import CLASSES_TO_COLLECT, EXISTING_CLASSES, MISSING_CLASSES
from config import DATA_DIR

print("="*60)
print("DRY RUN - Preview of Cleanup (NO FILES WILL BE DELETED)")
print("="*60)

print(f"\n📁 Scanning directory: {DATA_DIR}\n")

# Check existing classes (should be PROTECTED)
print("🔒 PROTECTED CLASSES (0-17) - Will NEVER be deleted:")
print("-" * 60)
existing_found = []
for class_id in sorted(EXISTING_CLASSES.keys()):
    folder_path = os.path.join(DATA_DIR, str(class_id))
    if os.path.exists(folder_path):
        try:
            image_count = len([f for f in os.listdir(folder_path) if f.endswith('.jpg')])
            existing_found.append((class_id, EXISTING_CLASSES[class_id], image_count))
            print(f"✅ Class {class_id:2d} - {EXISTING_CLASSES[class_id]:15s} : {image_count:3d} images - SAFE")
        except Exception as e:
            print(f"⚠️  Class {class_id:2d} - Error reading folder: {e}")
    else:
        print(f"⚠️  Class {class_id:2d} - {EXISTING_CLASSES[class_id]:15s} : Folder not found")

print(f"\n📊 Total protected: {len(existing_found)} classes with {sum(c[2] for c in existing_found)} images\n")

# Check newly collected classes (will be DELETED)
print("🗑️  NEWLY COLLECTED CLASSES - Will be deleted by cleanup:")
print("-" * 60)
new_found = []
for class_id in sorted(CLASSES_TO_COLLECT):
    folder_path = os.path.join(DATA_DIR, str(class_id))
    if os.path.exists(folder_path):
        try:
            image_count = len([f for f in os.listdir(folder_path) if f.endswith('.jpg')])
            new_found.append((class_id, MISSING_CLASSES[class_id], image_count))
            print(f"❌ Class {class_id:2d} - {MISSING_CLASSES[class_id]:15s} : {image_count:3d} images - WILL DELETE")
        except Exception as e:
            print(f"⚠️  Class {class_id:2d} - Error reading folder: {e}")

if not new_found:
    print("✅ No newly collected classes found - nothing to delete!")
else:
    print(f"\n📊 Total to delete: {len(new_found)} classes with {sum(c[2] for c in new_found)} images\n")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"✅ Protected (SAFE):  {len(existing_found)} classes, {sum(c[2] for c in existing_found) if existing_found else 0} images")
print(f"❌ Will Delete:       {len(new_found)} classes, {sum(c[2] for c in new_found) if new_found else 0} images")
print("\n" + "="*60)
print("This is a DRY RUN - NO files were deleted")
print("To actually delete, run: python cleanup_images.py")
print("="*60)
