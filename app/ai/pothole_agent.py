import ultralytics
from ultralytics import YOLO
import cv2
import torch
import os

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

def load_yolo_model_safely(weights_path: str):
    """Load YOLO model with proper PyTorch 2.6+ compatibility"""
    try:
        # Monkey patch torch.load to use weights_only=False for trusted model files
        original_load = torch.load
        def patched_load(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        
        # Temporarily patch torch.load
        torch.load = patched_load
        
        try:
            model = YOLO(weights_path)
            return model
        finally:
            # Restore original torch.load
            torch.load = original_load
            
    except Exception as e:
        raise Exception(f"Failed to load YOLO model from {weights_path}: {e}")


model = load_yolo_model_safely("app/ai/models/pothole.pt")

def get_confidence_and_severity(image_path):
    results = model(image_path)
    img = cv2.imread(image_path)
    H, W = img.shape[:2]
    img_area = H * W

    confidences = []
    total_area = 0

    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0])
            confidences.append(conf)

            # Bounding box area
            x1, y1, x2, y2 = box.xyxy[0]
            box_area = (x2 - x1) * (y2 - y1)
            total_area += box_area

    if len(confidences) == 0:
        return 0.0, 0.0   # No pothole detected

    # Overall confidence = max confidence
    overall_conf = max(confidences)

    # Severity = total pothole area / image area (normalized to 0–1)
    severity = min(total_area / img_area, 1.0)

    return overall_conf, severity
