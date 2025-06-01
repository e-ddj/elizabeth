#!/usr/bin/env python3
"""
Diagnostic tool to check OpenCV installation.
Run with: python scripts/check_opencv.py
"""

import sys
import os
import logging

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("opencv_check")

# System information
logger.info(f"Python version: {sys.version}")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Platform: {sys.platform}")

# Check environment variables
path = os.environ.get('PATH', '')
ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
logger.info(f"PATH: {path}")
logger.info(f"LD_LIBRARY_PATH: {ld_library_path}")

# Try importing OpenCV
try:
    import cv2
    cv2_version = cv2.__version__
    logger.info(f"✅ OpenCV imported successfully, version: {cv2_version}")
    
    # Check if haarcascades are available
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    logger.info(f"Cascade path: {cascade_path}")
    
    if os.path.exists(cascade_path):
        logger.info(f"✅ Face cascade file exists: {cascade_path}")
        
        # Try to load the cascade
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            logger.error("❌ Failed to load face cascade - file exists but couldn't be loaded")
        else:
            logger.info("✅ Face cascade loaded successfully")
            
            # Try to create a simple image and run face detection
            import numpy as np
            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
            gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            logger.info(f"✅ Face detection test completed: detected {len(faces)} faces in blank image (expected 0)")
    else:
        logger.error(f"❌ Face cascade file does not exist at: {cascade_path}")
        
except ImportError as e:
    logger.error(f"❌ Failed to import OpenCV: {e}")
    
    # Check if the package is installed
    try:
        import pkg_resources
        logger.info("Installed packages:")
        for pkg in pkg_resources.working_set:
            if "cv" in pkg.key or "opencv" in pkg.key:
                logger.info(f"  - {pkg.key} {pkg.version}")
    except Exception as e:
        logger.error(f"Failed to list installed packages: {e}")
        
except Exception as e:
    logger.error(f"❌ Error during OpenCV test: {e}")

logger.info("OpenCV check completed") 