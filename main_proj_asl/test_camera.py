"""
Quick Camera Test Script
Tests all available camera indices to find which one is your phone camera
"""

import cv2

print("="*60)
print("CAMERA INDEX FINDER")
print("="*60)
print("\nTesting camera indices 0-5...")
print("Press any key to move to next camera")
print("="*60)

working_cameras = []

for i in range(6):  # Test indices 0-5
    print(f"\n📹 Testing Camera Index: {i}")
    
    cap = cv2.VideoCapture(i)
    
    if cap.isOpened():
        ret, frame = cap.read()
        
        if ret and frame is not None:
            height, width = frame.shape[:2]
            print(f"   ✅ SUCCESS!")
            print(f"   Resolution: {width}x{height}")
            
            working_cameras.append({
                'index': i,
                'width': width,
                'height': height
            })
            
            # Show the camera feed
            cv2.putText(frame, f'Camera Index: {i}', (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            cv2.putText(frame, f'Resolution: {width}x{height}', (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            cv2.putText(frame, 'Press any key to continue...', (50, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            
            cv2.imshow('Camera Test', frame)
            print(f"   👀 Window opened - check if this is your phone camera!")
            cv2.waitKey(0)  # Wait for key press
            cv2.destroyAllWindows()
        else:
            print(f"   ❌ Camera opened but cannot read frames")
        
        cap.release()
    else:
        print(f"   ❌ Camera not available")

print("\n" + "="*60)
print("TEST COMPLETE!")
print("="*60)

if working_cameras:
    print(f"\n✅ Found {len(working_cameras)} working camera(s):")
    for cam in working_cameras:
        print(f"\n   Camera Index: {cam['index']}")
        print(f"   Resolution: {cam['width']}x{cam['height']}")
        if cam['index'] == 0:
            print(f"   → This is likely your INTERNAL/LAPTOP camera")
        else:
            print(f"   → This might be your EXTERNAL/PHONE camera")
    
    print("\n" + "="*60)
    print("RECOMMENDATION:")
    print("="*60)
    
    if len(working_cameras) > 1:
        external_cam = working_cameras[1]['index']
        print(f"\n🎯 Use Camera Index: {external_cam}")
        print(f"   (This is likely your phone camera)")
        print(f"\nUpdate your scripts with:")
        print(f"   cap = cv2.VideoCapture({external_cam})")
        print(f"\nOr in config.py:")
        print(f"   CAMERA_INDEX = {external_cam}")
    else:
        print(f"\n⚠️  Only one camera detected (index {working_cameras[0]['index']})")
        print(f"   Make sure your phone camera app is running!")
        print(f"\nTroubleshooting:")
        print(f"   1. Start DroidCam/iVCam on phone and PC")
        print(f"   2. Ensure USB debugging is enabled (Android)")
        print(f"   3. Check USB cable connection")
        print(f"   4. Restart this script")
else:
    print("\n❌ No working cameras found!")
    print("\nTroubleshooting:")
    print("   1. Check if any camera app is open")
    print("   2. Connect phone camera via USB")
    print("   3. Install DroidCam/iVCam")
    print("   4. Check Windows camera permissions")

print("\n" + "="*60)
