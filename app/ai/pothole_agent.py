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
    severity_area_sum = 0.0
    severity_count_sum = 0.0

    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0])
            confidences.append(conf)

            # Bounding box area
            x1, y1, x2, y2 = box.xyxy[0]
            box_area = (x2 - x1) * (y2 - y1)

            # Area-based contribution (relative size of pothole)
            severity_area_sum += (box_area / img_area) * conf

            # Count-based contribution (each pothole matters, even if small)
            severity_count_sum += 0.1 * conf  # tweak factor → importance of count

    if not confidences:
        return 0.0, 0.0   # No pothole detected

    overall_conf = max(confidences)

    # Combine area + count contributions
    severity = severity_area_sum + severity_count_sum

    # Cap to [0, 1]
    severity = min(severity, 1.0)

    return overall_conf, severity