from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import os
import uuid


def optimize_image(image_field, max_size=(1920, 1080), quality=85, format='JPEG'):
    """
    Optimize an image by resizing and compressing it.
    
    Args:
        image_field: Django ImageField instance
        max_size: Tuple of maximum (width, height)
        quality: JPEG quality (1-100)
        format: Output format ('JPEG', 'PNG', 'WEBP')
    
    Returns:
        ContentFile: Optimized image file
    """
    try:
        # Open the image
        with Image.open(image_field) as img:
            # Auto-orient based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Convert to RGB if necessary (for JPEG output)
            if format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if larger than max_size
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save to BytesIO
            output = BytesIO()
            save_kwargs = {'format': format}
            
            if format == 'JPEG':
                save_kwargs.update({
                    'quality': quality,
                    'optimize': True,
                    'progressive': True
                })
            elif format == 'PNG':
                save_kwargs.update({
                    'optimize': True
                })
            elif format == 'WEBP':
                save_kwargs.update({
                    'quality': quality,
                    'optimize': True
                })
            
            img.save(output, **save_kwargs)
            output.seek(0)
            
            # Generate new filename
            original_name = os.path.splitext(image_field.name)[0]
            extension_map = {'JPEG': '.jpg', 'PNG': '.png', 'WEBP': '.webp'}
            new_extension = extension_map.get(format, '.jpg')
            new_filename = f"{original_name}_optimized{new_extension}"
            
            return ContentFile(output.getvalue(), name=new_filename)
            
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return None


def create_thumbnail(image_field, size=(300, 300), quality=80):
    """
    Create a thumbnail for an image.
    
    Args:
        image_field: Django ImageField instance
        size: Tuple of thumbnail (width, height)
        quality: JPEG quality for thumbnail
    
    Returns:
        ContentFile: Thumbnail image file
    """
    try:
        with Image.open(image_field) as img:
            # Auto-orient based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Create a new image with the exact thumbnail size and center the resized image
            thumbnail = Image.new('RGB', size, (255, 255, 255))
            
            # Calculate position to center the image
            x = (size[0] - img.size[0]) // 2
            y = (size[1] - img.size[1]) // 2
            
            thumbnail.paste(img, (x, y))
            
            # Save to BytesIO
            output = BytesIO()
            thumbnail.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Generate thumbnail filename
            original_name = os.path.splitext(image_field.name)[0]
            thumbnail_filename = f"{original_name}_thumb.jpg"
            
            return ContentFile(output.getvalue(), name=thumbnail_filename)
            
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None


def process_gallery_image(image_file, title=None):
    """
    Complete processing pipeline for a gallery image.
    
    Args:
        image_file: Uploaded image file
        title: Optional title for the image
    
    Returns:
        dict: Contains 'optimized_image' and 'thumbnail' ContentFile objects
    """
    result = {
        'optimized_image': None,
        'thumbnail': None,
        'original_dimensions': None,
        'optimized_dimensions': None
    }
    
    try:
        # Get original dimensions
        with Image.open(image_file) as img:
            result['original_dimensions'] = img.size
        
        # Reset file pointer
        image_file.seek(0)
        
        # Optimize the main image
        optimized = optimize_image(image_file, max_size=(1920, 1080), quality=85)
        if optimized:
            result['optimized_image'] = optimized
            
            # Get optimized dimensions
            with Image.open(optimized) as img:
                result['optimized_dimensions'] = img.size
        
        # Reset file pointer for thumbnail creation
        image_file.seek(0)
        
        # Create thumbnail
        thumbnail = create_thumbnail(image_file, size=(300, 300), quality=80)
        if thumbnail:
            result['thumbnail'] = thumbnail
            
    except Exception as e:
        print(f"Error processing gallery image: {e}")
    
    return result


def generate_unique_filename(original_filename, prefix="gallery"):
    """
    Generate a unique filename for uploaded images.
    
    Args:
        original_filename: Original filename
        prefix: Prefix for the new filename
    
    Returns:
        str: Unique filename
    """
    # Extract extension
    name, ext = os.path.splitext(original_filename)
    
    # Generate unique identifier
    unique_id = str(uuid.uuid4())[:8]
    
    # Clean the original name (remove special characters)
    clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_name = clean_name.replace(' ', '_')
    
    # Construct new filename
    new_filename = f"{prefix}_{clean_name}_{unique_id}{ext.lower()}"
    
    return new_filename


def get_image_info(image_file):
    """
    Get information about an image file.
    
    Args:
        image_file: Image file object
    
    Returns:
        dict: Image information
    """
    try:
        with Image.open(image_file) as img:
            return {
                'size': img.size,
                'format': img.format,
                'mode': img.mode,
                'file_size': image_file.size,
                'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
    except Exception as e:
        return {'error': str(e)}
