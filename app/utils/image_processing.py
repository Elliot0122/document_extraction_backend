from PIL import Image, ImageDraw
import io
import base64

def circle_the_info_on_image(image_bytes: bytes, geometry: dict = None) -> str:
    """Draw a red rectangle with rounded corners on the image and return base64 encoded image."""
    # Open the image from bytes
    image = Image.open(io.BytesIO(image_bytes))
    
    # Create a drawing object
    draw = ImageDraw.Draw(image)
    
    # Get image dimensions
    width, height = image.size
    
    if geometry:
        # Draw rectangle at the detected location
        left = int(geometry.get("Left", 0) * width) - 3
        top = int(geometry.get("Top", 0) * height) - 3
        right = int((geometry.get("Left", 0) + geometry.get("Width", 0)) * width) + 3
        bottom = int((geometry.get("Top", 0) + geometry.get("Height", 0)) * height) + 3
        
        # Calculate corner radius (10% of the smaller dimension)
        corner_radius = min(right - left, bottom - top) // 10
        
        # Draw the rectangle with rounded corners
        draw.rounded_rectangle(
            [left, top, right, bottom],
            radius=corner_radius,
            outline='red',
            width=3
        )

    
    # Save the modified image to bytes
    output = io.BytesIO()
    image.save(output, format='PNG')
    return base64.b64encode(output.getvalue()).decode('utf-8')