#!/usr/bin/env python3
"""
Simple script to test OpenCV installation
"""

import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable path: {sys.executable}")

try:
    import cv2
    print(f"OpenCV successfully imported, version: {cv2.__version__}")
    
    # Test if haarcascades are available
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    print(f"Cascade path: {cascade_path}")
    
    if os.path.exists(cascade_path):
        print(f"Face cascade file exists at: {cascade_path}")
        
        # Try to load the cascade
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            print("Failed to load face cascade - file exists but couldn't be loaded")
        else:
            print("Face cascade loaded successfully")
            
            # Test simple image operation
            import numpy as np
            test_img = np.zeros((10, 10, 3), dtype=np.uint8)
            gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            print("Successfully converted test image to grayscale")
    else:
        print(f"Face cascade file does not exist at: {cascade_path}")
        
except ImportError as e:
    print(f"Failed to import OpenCV: {e}")
except Exception as e:
    print(f"Error during OpenCV test: {e}")

print("OpenCV test completed") 