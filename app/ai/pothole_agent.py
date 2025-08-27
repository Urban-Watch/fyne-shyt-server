import ultralytics
from ultralytics import YOLO
import cv2

def get_confidence_and_severity(results, image_path):
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
