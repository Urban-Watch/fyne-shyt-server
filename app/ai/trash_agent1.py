from ultralytics import YOLO
import cv2
import torch
import os

# Set up PyTorch to allow loading of trusted model files
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

RECYCLABLE = ['cardboard_box','can','plastic_bottle_cap','plastic_bottle','reuseable_paper']
NON_RECYCLABLE = ['plastic_bag','scrap_paper','stick','plastic_cup','snack_bag','plastic_box','straw',
                  'plastic_cup_lid','scrap_plastic','cardboard_bowl','plastic_cultery']
HAZARDOUS = ['battery','chemical_spray_can','chemical_plastic_bottle','chemical_plastic_gallon',
             'light_bulb','paint_bucket']

CATEGORY_WEIGHTS = {
    "recyclable": 0.5,
    "non_recyclable": 0.7,
    "hazardous": 1.0
}

model = load_yolo_model_safely("app/ai/models/trash_new.pt")

def get_category(label):
    if label in RECYCLABLE:
        return "recyclable"
    elif label in NON_RECYCLABLE:
        return "non_recyclable"
    elif label in HAZARDOUS:
        return "hazardous"
    else:
        return "unknown"

def analyze_waste(image_path):
    results = model(image_path)
    img = cv2.imread(image_path)
    H, W = img.shape[:2]
    img_area = H * W

    confidences = []
    severity_area_sum = 0.0
    severity_count_sum = 0.0
    hazardous_detected = False

    for result in results:
        names = result.names
        for box in result.boxes:
            cls = int(box.cls[0])
            label = names[cls]
            conf = float(box.conf[0])
            confidences.append(conf)

            x1, y1, x2, y2 = box.xyxy[0]
            box_area = (x2 - x1) * (y2 - y1)

            category = get_category(label)
            weight = CATEGORY_WEIGHTS.get(category, 0.5)

            # Area-based severity (proportional to image area)
            severity_area_sum += (box_area / img_area) * weight * conf

            # Count-based severity (each item matters)
            severity_count_sum += 0.05 * weight * conf  # tweak factor 0.05 → controls importance of count

            # Hazardous override check
            if category == "hazardous" and conf > 0.5:
                hazardous_detected = True

    if not confidences:
        return 0.0, 0.0

    overall_conf = max(confidences)

    # Combine area + count contributions
    severity = severity_area_sum + severity_count_sum

    # Cap to [0, 1]
    severity = min(severity, 1.0)

    # Hazardous items boost severity minimum
    if hazardous_detected:
        severity = max(severity, 0.6)

    return overall_conf, severity

