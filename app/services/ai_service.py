import os
import sys
import tempfile
import json
import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import io

# Add the app directory to path so we can import the AI modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.ai.final import process_image as process_image_ai
from app.ai.criticality_score import compute_criticality_score
from app.ai.impact import calculate_impact_score

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIService:
    """Service for processing images and calculating criticality scores"""

    def __init__(self):
        pass

    async def process_report_image(
        self,
        image_data: bytes,
        latitude: float,
        longitude: float,
        address: str = "Unknown location",
        age_seconds: Optional[float] = None,
        report_count: int = 1
    ) -> Dict[str, Any]:
        """
        Complete AI processing pipeline for a report

        Args:
            image_data: Raw image bytes
            latitude: Location latitude
            longitude: Location longitude
            address: Human-readable address of the location
            age_seconds: How old the report is (optional)
            report_count: Number of duplicate reports

        Returns:
            Dict containing all AI analysis results
        """

        logger.info("=== AI SERVICE PIPELINE STARTED ===")
        logger.info(f"Input parameters: image_size={len(image_data)} bytes, lat={latitude}, lon={longitude}, age_seconds={age_seconds}, report_count={report_count}")
        logger.info(f"Full address: {address}")

        # Validate image data
        if not image_data or len(image_data) == 0:
            error_msg = "Image data is empty or missing"
            logger.error(f"Image validation failed: {error_msg}")
            raise ValueError(error_msg)

        logger.info(f"Image data size: {len(image_data)} bytes")

        # Step 1: Convert image bytes to PIL Image
        logger.info("Step 1: Converting image bytes to PIL Image")
        image = Image.open(io.BytesIO(image_data))
        logger.info(f"Image converted successfully: size={image.size}, mode={image.mode}, format={image.format}")

        # Validate image format - check PIL format
        valid_formats = ['JPEG', 'PNG', 'WEBP', 'JPG']
        if image.format and image.format.upper() not in valid_formats:
            error_msg = f"Unsupported image format: {image.format} (valid formats: {valid_formats})"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Image validation completed successfully")

        # Step 2: Process image through final.py for basic analysis
        logger.info("Step 2: Processing image through final.py for AI analysis")
        try:
            image_analysis = process_image_ai(image, address=address)
        except Exception as e:
            logger.error(f"AI processing failed in final.py: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise RuntimeError(f"AI processing failed: {str(e)}")

        if "error" in image_analysis:
            # AI processing failed - raise exception instead of returning fallback data
            error_msg = f"AI analysis failed: {image_analysis['error']}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Image analysis successful: {image_analysis}")

        # Step 3: Calculate impact score using location
        logger.info("Step 3: Calculating impact score using location data")
        impact_result = calculate_impact_score(
            lat=latitude,
            lon=longitude,
            radius_km=1.0
        )
        logger.info(f"Impact calculation result: {impact_result}")

        # Step 4: Calculate final criticality score
        logger.info("Step 4: Calculating final criticality score")
        criticality_result = compute_criticality_score(
            severity=image_analysis["severity_score"],  # Convert 1-100 to 0-1 scale for calculation
            impact=impact_result["impact_score"],               # 1-100 scale
            age_seconds=age_seconds,
            report_count=report_count
        )
        logger.info(f"Criticality calculation result: {criticality_result}")

        # Step 5: Combine all results
        logger.info("Step 5: Combining all AI analysis results")
        final_result = {
            "severity_score": image_analysis["severity_score"],
            "category": image_analysis["category"],
            "title": image_analysis["title"],
            "description": image_analysis["description"],
            "criticality_score": criticality_result["criticality"],
            "impact_score": impact_result["impact_score"],
            "population_estimate": impact_result.get("population_estimate"),
            "vehicle_estimate": impact_result.get("vehicle_estimate"),
            "ai_analysis_success": True,
            "criticality_components": criticality_result["components"]
        }

        logger.info("=== AI SERVICE PIPELINE COMPLETED SUCCESSFULLY ===")
        logger.info(f"Final combined result: {final_result}")
        return final_result

# Global instance
ai_service = AIService()