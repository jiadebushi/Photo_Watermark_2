"""Test transparency preservation"""

from PIL import Image, ImageDraw
from text_watermark_manager import TextWatermarkManager
from image_processor import ImageProcessor

print("Testing transparency preservation...")

# Create test image with transparency
width, height = 400, 300
test_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))

# Draw a red circle in the center
draw = ImageDraw.Draw(test_image)
draw.ellipse([100, 75, 300, 225], fill=(255, 0, 0, 255))

test_image.save('test_original.png', 'PNG')
print(f"Created test image: {test_image.mode}, size: {test_image.size}")

# Add watermark
manager = TextWatermarkManager()
watermarked = manager.preview_watermark(
    test_image,
    text="TEST",
    font_family="Arial",
    font_size=36,
    color="#FFFFFF",
    opacity=80,
    position="bottom_right",
    max_preview_size=(10000, 10000),
    for_display=False  # Preserve transparency
)

print(f"After watermark: {watermarked.mode}, size: {watermarked.size}")
watermarked.save('test_watermarked.png', 'PNG')

# Verify transparency
if watermarked.mode == 'RGBA':
    # Check corners for transparency
    corners = [(0, 0), (width-1, 0), (0, height-1)]
    
    all_transparent = True
    for x, y in corners:
        pixel = watermarked.getpixel((x, y))
        if pixel[3] != 0:
            all_transparent = False
            print(f"Corner ({x}, {y}) is NOT transparent: {pixel}")
    
    if all_transparent:
        print("SUCCESS: Transparency preserved! Corners are transparent.")
    else:
        print("FAILED: Transparency lost!")
else:
    print(f"FAILED: Wrong mode: {watermarked.mode}, should be RGBA")

# Test save function
print("\nTesting save function...")
test_image2 = Image.new('RGBA', (200, 200), (0, 255, 0, 128))
processor = ImageProcessor()
success = processor.save_image(test_image2, 'test_save_png.png', 'PNG')

if success:
    loaded = Image.open('test_save_png.png')
    if loaded.mode == 'RGBA':
        pixel = loaded.getpixel((100, 100))
        if pixel[3] < 255:
            print(f"SUCCESS: PNG transparency saved: pixel = {pixel}")
        else:
            print(f"FAILED: PNG transparency lost: pixel = {pixel}")
    else:
        print(f"FAILED: PNG wrong mode: {loaded.mode}")
else:
    print("FAILED: PNG save failed")

print("\nTest files created:")
print("  - test_original.png")
print("  - test_watermarked.png")
print("  - test_save_png.png")

