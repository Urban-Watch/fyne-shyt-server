import os
import cv2
import json
import concurrent.futures
import tempfile
import io
import PIL.Image
import logging
import torch
from ultralytics import YOLO
# Make sure these local modules are in your project directory
from .pothole_agent import get_confidence_and_severity as pothole_infer
from .trash_agent1 import analyze_waste

import google.generativeai as genai
from dotenv import load_dotenv

# Load .env file (for GOOGLE_API_KEY)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment variable to allow loading of older PyTorch models
# This is safe for trusted model files like our own trained models
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

def load_yolo_model_safely(weights_path: str):
    """Load YOLO model with proper PyTorch 2.6+ compatibility"""
    try:
        # For trusted model files, we need to handle the weights_only change in PyTorch 2.6
        logger.info(f"Loading YOLO model from {weights_path}")
        
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
            logger.info(f"Successfully loaded YOLO model from {weights_path}")
            return model
        finally:
            # Restore original torch.load
            torch.load = original_load
            
    except Exception as e:
        logger.error(f"Failed to load YOLO model from {weights_path}: {e}")
        raise

def process_image(image, address="Unknown location", pothole_weights="app/ai/models/pothole.pt", trash_weights="app/ai/models/trash_new.pt"):
    """
    Process image for urban monitoring
    Args:
        image: PIL Image object or bytes
        address: Human-readable address of the location
    Returns:
        dict with severity_score, category, title, description
    """
    logger.info("=== FINAL.PY PROCESS_IMAGE STARTED ===")
    logger.info(f"Input: image type={type(image)}, pothole_weights={pothole_weights}, trash_weights={trash_weights}")
    logger.info(f"Address: {address}")

    results = {}

    # Handle different image input types
    temp_path = None
    try:
        if isinstance(image, PIL.Image.Image):
            # Save PIL image to temporary file for YOLO processing
            temp_path = tempfile.mktemp(suffix='.jpg')
            image.save(temp_path)
            pil_image = image
            logger.info(f"Input image: PIL Image, saved to temp path: {temp_path}")
        elif isinstance(image, bytes):
            # Convert bytes to PIL image
            pil_image = PIL.Image.open(io.BytesIO(image))
            temp_path = tempfile.mktemp(suffix='.jpg')
            pil_image.save(temp_path)
            logger.info(f"Input image: bytes ({len(image)} bytes), converted to PIL and saved to temp path: {temp_path}")
        else:
            error_msg = f"Unsupported image format: {type(image)}"
            logger.error(error_msg)
            return {"error": error_msg}

        image_path = temp_path
        logger.info(f"Image path for processing: {image_path}")

        # Run pothole & trash in parallel
        logger.info("Starting parallel AI inference for pothole and trash detection")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            pothole_future = executor.submit(
                lambda: pothole_infer(image_path)
            )
            trash_future = executor.submit(
                lambda: analyze_waste(image_path)
            )

            pothole_conf_tensor, pothole_sev_tensor = pothole_future.result()
            trash_conf_tensor, trash_sev_tensor = trash_future.result()

        # Convert potential Tensor objects to standard Python floats
        pothole_conf = pothole_conf_tensor.item() if hasattr(pothole_conf_tensor, 'item') else pothole_conf_tensor
        pothole_sev = pothole_sev_tensor.item() if hasattr(pothole_sev_tensor, 'item') else pothole_sev_tensor
        trash_conf = trash_conf_tensor.item() if hasattr(trash_conf_tensor, 'item') else trash_conf_tensor
        trash_sev = trash_sev_tensor.item() if hasattr(trash_sev_tensor, 'item') else trash_sev_tensor

        logger.info(f"AI Inference Results:")
        logger.info(f"  Pothole - Confidence: {pothole_conf:.4f}, Severity: {pothole_sev:.4f}")
        logger.info(f"  Trash - Confidence: {trash_conf:.4f}, Severity: {trash_sev:.4f}")

        # --- Calculate overall metrics ---
        severity_score_float = (0.6 * pothole_sev + 0.4 * trash_sev)
        overall_confidence = (pothole_conf + trash_conf) / 2

            # --- Calculate overall metrics (threshold-based) ---
        if (pothole_sev >= 0.7 and pothole_conf >= 0.6) or (trash_sev >= 0.7 and trash_conf >= 0.6):
            # If either hazard is clearly severe & confident
            severity_score_float = max(pothole_sev, trash_sev)
            overall_confidence = max(pothole_conf, trash_conf)

        elif pothole_sev >= 0.4 and trash_sev >= 0.4:
            # Both moderately severe → escalate
            severity_score_float = (pothole_sev + trash_sev) / 2 + 0.2
            severity_score_float = min(severity_score_float, 1.0)  # cap at 1
            overall_confidence = (pothole_conf + trash_conf) / 2

        else:
            # Otherwise, use weighted contribution but scale by confidence
            weighted_pothole = pothole_sev * pothole_conf
            weighted_trash = trash_sev * trash_conf
            severity_score_float = min(weighted_pothole + weighted_trash, 1.0)

            # Confidence favors whichever issue is more severe
            if pothole_sev > trash_sev:
                overall_confidence = pothole_conf
            else:
                overall_confidence = trash_conf


        # Convert 0-1 scale to 1-100 and use ceiling to ensure minimum value of 1
        import math
        severity_score = max(1, math.ceil(severity_score_float * 100))
        logger.info(f"Calculated overall severity score: {severity_score_float:.4f} -> {severity_score} (1-100 scale)")

        # Determine category based on confidences
        if pothole_conf > trash_conf and pothole_conf > 0.5:
            category = "potholes"
        elif trash_conf > pothole_conf and trash_conf > 0.5:
            category = "trash_overflow"
        elif pothole_conf > 0.3 and trash_conf > 0.3:
            # For mixed cases, choose the one with higher confidence
            category = "potholes" if pothole_conf > trash_conf else "trash_overflow"
        else:
            # Default to potholes if neither meets threshold clearly
            category = "potholes"

        logger.info(f"Determined category: {category}")
        logger.info(f"Category decision logic: pothole_conf={pothole_conf:.4f}, trash_conf={trash_conf:.4f}")

        # Gemini for title and description
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            error_msg = "No GOOGLE_API_KEY found"
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info("Configuring Gemini API and generating content description")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        prompt = f"""You are an urban street monitoring assistant analyzing an image and location data. 

LOCATION: {address}

ANALYSIS RESULTS:
- Pothole Detection: Severity={pothole_sev:.2f}, Confidence={pothole_conf:.2f}  
- Trash Detection: Severity={trash_sev:.2f}, Confidence={trash_conf:.2f}
- Overall Severity Score: {severity_score_float:.2f}
- Primary Issue Category: {category}

INSTRUCTIONS:
Look at the provided image and combine it with the location information above. Generate a response in EXACTLY this format (no additional text):

TITLE: [Descriptive title, max 8 words, include location context]
DESCRIPTION: [Detailed 3-4 line description of what you see in the image at this specific location. Describe the severity, visual details, and potential community impact. Reference the location when relevant.]

Respond ONLY with TITLE and DESCRIPTION sections. No other text."""

        logger.info("Configuring Gemini API and generating content description")
        logger.info("Gemini Prompt:")
        logger.info(prompt)
        logger.info("Sending prompt + image to Gemini...")
        response = model.generate_content([prompt, pil_image])
        response_text = response.text.strip()
        logger.info(f"Gemini Response: {response_text}")

        # Parse title and description from response
        title = "Urban Issue Detected"
        description = response_text

        if "TITLE:" in response_text and "DESCRIPTION:" in response_text:
            parts = response_text.split("DESCRIPTION:")
            if len(parts) >= 2:
                title_part = parts[0].replace("TITLE:", "").strip()
                description = parts[1].strip()
                if title_part:
                    title = title_part
                logger.info(f"Parsed Title: '{title}'")
                logger.info(f"Parsed Description: '{description[:100]}...'")

        final_result = {
            "severity_score": severity_score,  # Now integer 1-100
            "category": category,
            "title": title,
            "description": description
        }

        logger.info(f"=== FINAL.PY PROCESS_IMAGE COMPLETED ===")
        logger.info(f"Final Output: {final_result}")
        return final_result

    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        logger.error(f"=== FINAL.PY PROCESS_IMAGE ERROR ===")
        logger.error(error_msg)
        logger.error(f"Exception type: {type(e).__name__}")
        return {"error": error_msg}
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
            logger.info(f"Cleaned up temporary file: {temp_path}")

# # --- Example Run ---
# if __name__ == "__main__":
#     # Example with PIL Image
#     img_path = "./test0.avif"
#     try:
#         pil_img = PIL.Image.open(img_path)
#         output = process_image(pil_img)
#         print(json.dumps(output, indent=2))
#     except FileNotFoundError:
#         print("Example image not found - this is expected in different environments")
#         print("Function now accepts PIL Image objects instead of file paths")