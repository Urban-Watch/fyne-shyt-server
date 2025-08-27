import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import io
from app.core.config import settings
from app.db.supabase_client import get_supabase_service_client
import logging

logger = logging.getLogger(__name__)

class ImageService:
    """Service for handling image uploads and storage"""
    
    def __init__(self):
        self.bucket_name = settings.SUPABASE_STORAGE_BUCKET
        self.supabase_client = get_supabase_service_client()
    
    
    def validate_image(self, file: UploadFile) -> bool:
        """Validate image file"""
        logger.info(f"Validating image: {file.filename}, size: {file.size}, content_type: {file.content_type}")
        
        # Check file size
        if file.size and file.size > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Image size too large. Maximum size is {settings.MAX_IMAGE_SIZE / (1024 * 1024):.1f}MB"
            )
        
        # Check content type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            logger.warning(f"Invalid content type: {file.content_type}, allowed: {settings.ALLOWED_IMAGE_TYPES}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )
        
        logger.info("Image validation passed")
        return True
    
    async def save_image_from_data(self, file: UploadFile, image_data: bytes) -> str:
        """Upload image to Supabase storage using pre-read image data and return public URL"""
        try:
            if not self.supabase_client:
                raise HTTPException(status_code=500, detail="Supabase client not available")
            
            # Validate image
            self.validate_image(file)
            
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            logger.info(f"Using pre-read image data: {len(image_data)} bytes")
            
            # Validate it's actually an image using the provided data
            try:
                with Image.open(io.BytesIO(image_data)) as img:
                    img.verify()
                    logger.info(f"PIL image verification passed: size={img.size}, mode={img.mode}, format={img.format}")
            except Exception as e:
                logger.error(f"PIL image verification failed: {e}")
                raise HTTPException(status_code=400, detail="Invalid image file")
            
            # Skip optimization to preserve original format for AI processing
            logger.info("Skipping image optimization to preserve original format for AI processing")
            optimized_content = image_data
            
            # Upload to Supabase storage
            result = self.supabase_client.storage.from_(self.bucket_name).upload(
                path=unique_filename,
                file=optimized_content
            )
            
            if result.status_code not in [200, 201]:
                raise HTTPException(status_code=500, detail="Failed to upload image to storage")
            
            # Get public URL
            public_url_response = self.supabase_client.storage.from_(self.bucket_name).get_public_url(unique_filename)
            
            if not public_url_response:
                raise HTTPException(status_code=500, detail="Failed to get public URL")
            
            logger.info(f"Image uploaded to Supabase: {unique_filename}")
            return public_url_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading image to Supabase: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image")
    
    async def save_image(self, file: UploadFile) -> str:
        """Upload image to Supabase storage and return public URL"""
        try:
            if not self.supabase_client:
                raise HTTPException(status_code=500, detail="Supabase client not available")
            
            # Validate image
            self.validate_image(file)
            
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Read file content
            content = await file.read()
            logger.info(f"Read {len(content)} bytes of image content")
            
            # Validate it's actually an image
            try:
                with Image.open(io.BytesIO(content)) as img:
                    img.verify()
                    logger.info(f"PIL image verification passed: size={img.size}, mode={img.mode}, format={img.format}")
            except Exception as e:
                logger.error(f"PIL image verification failed: {e}")
                raise HTTPException(status_code=400, detail="Invalid image file")
            
            # Reset file pointer and optimize image
            # For now, skip optimization to avoid potential issues with AI processing
            logger.info("Skipping image optimization to preserve original format for AI processing")
            optimized_content = content
            
            # Upload to Supabase storage
            result = self.supabase_client.storage.from_(self.bucket_name).upload(
                path=unique_filename,
                file=optimized_content
            )
            
            if result.status_code not in [200, 201]:
                raise HTTPException(status_code=500, detail="Failed to upload image to storage")
            
            # Get public URL
            public_url_response = self.supabase_client.storage.from_(self.bucket_name).get_public_url(unique_filename)
            
            if not public_url_response:
                raise HTTPException(status_code=500, detail="Failed to get public URL")
            
            logger.info(f"Image uploaded to Supabase: {unique_filename}")
            return public_url_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading image to Supabase: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image")
    
    async def save_multiple_images(self, files: List[UploadFile]) -> List[str]:
        """Save multiple images to Supabase and return list of public URLs"""
        image_urls = []
        
        for file in files:
            try:
                image_url = await self.save_image(file)
                image_urls.append(image_url)
            except Exception as e:
                # Clean up any successfully uploaded images
                for uploaded_url in image_urls:
                    await self.delete_from_supabase(uploaded_url)
                raise
        
        return image_urls
    
    async def delete_from_supabase(self, image_url: str) -> bool:
        """Delete image from Supabase storage using the public URL"""
        try:
            if not self.supabase_client:
                logger.warning("Supabase client not available for deletion")
                return False
            
            logger.info(f"Original image URL: {image_url}")
            
            # Extract filename from URL - handle various URL formats
            # URL format examples:
            # https://bucket.supabase.co/storage/v1/object/public/bucket_name/filename.jpg
            # https://bucket.supabase.co/storage/v1/object/public/bucket_name/filename.jpg?token=...
            
            # Split by '/' and get the last part
            url_parts = image_url.split('/')
            filename_with_params = url_parts[-1]
            
            # Remove query parameters if present (everything after '?')
            filename = filename_with_params.split('?')[0]
            
            logger.info(f"Extracted filename: '{filename}' from URL part: '{filename_with_params}'")
            
            # Additional validation - ensure we have a valid filename
            if not filename or '.' not in filename:
                logger.error(f"Invalid filename extracted: '{filename}'")
                return False
            
            # Delete from Supabase storage
            logger.info(f"Calling Supabase remove for filename: {filename}")
            result = self.supabase_client.storage.from_(self.bucket_name).remove([filename])
            
            logger.info(f"Supabase remove result: {result}")
            
            # Check if deletion was successful
            if result and isinstance(result, list) and len(result) > 0:
                # Supabase returns a list with deletion results
                deletion_result = result[0]
                logger.info(f"Deletion result details: {deletion_result}")
                
                if isinstance(deletion_result, dict):
                    if deletion_result.get('name') == filename or 'error' not in deletion_result:
                        logger.info(f"Image deleted from Supabase: {filename}")
                        return True
                    else:
                        logger.warning(f"Deletion failed with result: {deletion_result}")
                        return False
                else:
                    logger.warning(f"Unexpected deletion result type: {type(deletion_result)}")
                    return False
            else:
                logger.warning(f"Failed to delete image from Supabase: {filename} - empty or invalid result")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image from Supabase {image_url}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _optimize_image_content(self, content: bytes) -> bytes:
        """Optimize image content for storage"""
        try:
            logger.info("Starting image optimization")
            with Image.open(io.BytesIO(content)) as img:
                original_size = img.size
                original_mode = img.mode
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                    logger.info(f"Converted image from {original_mode} to RGB")
                
                # Resize if too large
                max_width, max_height = 1920, 1080
                if img.size[0] > max_width or img.size[1] > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image from {original_size} to {img.size}")
                
                # Save optimized image to bytes
                output = io.BytesIO()
                img.save(output, 'JPEG', quality=85, optimize=True)
                optimized_content = output.getvalue()
                
                logger.info(f"Image optimization completed: {len(content)} -> {len(optimized_content)} bytes")
                return optimized_content
                
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            logger.info("Returning original content due to optimization failure")
            return content  # Return original if optimization fails

# Global image service instance
image_service = ImageService()
