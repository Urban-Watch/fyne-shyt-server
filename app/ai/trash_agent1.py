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
    """
    Run YOLOv8 inference on a waste image and compute overall confidence and severity.
    """
    # Load model safely
    model = load_yolo_model_safely("app/ai/models/trash_new.pt")

    # Run inference
    results = model(image_path)

    # Load image to calculate areas
    img = cv2.imread(image_path)
    H, W = img.shape[:2]
    img_area = H * W

    confidences = []
    weighted_area = 0

    for result in results:
        names = result.names  # class id -> label mapping
        for box in result.boxes:
            cls = int(box.cls[0])
            label = names[cls]
            conf = float(box.conf[0])
            confidences.append(conf)

            # bounding box area
            x1, y1, x2, y2 = box.xyxy[0]
            box_area = (x2 - x1) * (y2 - y1)

            # category weight
            category = get_category(label)
            weight = CATEGORY_WEIGHTS.get(category, 0.5)

            weighted_area += box_area * weight

    if len(confidences) == 0:
        return 0.0, 0.0

    # confidence = max detection confidence
    overall_conf = max(confidences)

    # severity = weighted area / image area (clamped 0–1)
    severity = min(weighted_area / img_area, 1.0)

    return overall_conf, severity
