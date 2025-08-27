"""
Geocoding service for reverse geocoding location coordinates to human-readable addresses.
"""
import logging
from typing import Optional
from geopy.geocoders import Nominatim

# Configure logging
logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self):
        # Initialize Nominatim geocoder with a user agent
        self.geocoder = Nominatim(user_agent="urban-watch-server")
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Convert latitude and longitude to a human-readable address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Human-readable address string or None if geocoding fails
        """
        try:
            logger.info(f"Reverse geocoding coordinates: lat={latitude}, lon={longitude}")
            
            # Perform reverse geocoding
            location = self.geocoder.reverse((latitude, longitude))
            
            if location and hasattr(location, 'address') and location.address:
                address = str(location.address)
                logger.info(f"Reverse geocoding successful: {address}")
                return address
            else:
                logger.warning(f"No address found for coordinates: lat={latitude}, lon={longitude}")
                return None
                
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {e}")
            return None

# Global instance
geocoding_service = GeocodingService()
