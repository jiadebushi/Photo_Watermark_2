"""
测试透明通道保留功能
验证PNG图片的透明部分在添加水印后仍然保持透明
"""

from PIL import Image
import numpy as np
from text_watermark_manager import TextWatermarkManager
from image_processor import ImageProcessor

def test_text_watermark_transparency():
    """测试文本水印是否保留透明通道"""
    print("测试文本水印透明通道保留...")
    
    # 创建一个带透明通道的测试图片
    width, height = 400, 300
    test_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # 在中间画一个红色圆圈（不透明）
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_image)
    draw.ellipse([100, 75, 300, 225], fill=(255, 0, 0, 255))
    
    # 保存原始图片
    test_image.save('test_original.png', 'PNG')
    print(f"✓ 创建测试图片: {test_image.mode}, 尺寸: {test_image.size}")
    
    # 使用文本水印管理器添加水印
    manager = TextWatermarkManager()
    
    # 添加水印（用于保存，不用于显示）
    watermarked = manager.preview_watermark(
        test_image,
        text="TEST",
        font_family="Arial",
        font_size=36,
        color="#FFFFFF",
        opacity=80,
        position="bottom_right",
        max_preview_size=(10000, 10000),
        for_display=False  # 保持透明通道
    )
    
    print(f"✓ 添加水印后: {watermarked.mode}, 尺寸: {watermarked.size}")
    
    # 保存带水印的图片
    watermarked.save('test_watermarked.png', 'PNG')
    
    # 验证透明通道是否保留
    if watermarked.mode == 'RGBA':
        # 检查图片四角的透明度
        corners = [
            (0, 0),  # 左上
            (width-1, 0),  # 右上
            (0, height-1),  # 左下
            # 右下角有水印，不检查
        ]
        
        all_transparent = True
        for x, y in corners:
            pixel = watermarked.getpixel((x, y))
            if pixel[3] != 0:  # Alpha通道应该为0（完全透明）
                all_transparent = False
                print(f"✗ 位置 ({x}, {y}) 不透明: {pixel}")
        
        if all_transparent:
            print("✓ 透明通道保留成功！图片四角保持透明")
            print("✓ 测试通过！")
            return True
        else:
            print("✗ 透明通道丢失，透明部分变成了不透明")
            return False
    else:
        print(f"✗ 图片模式错误: {watermarked.mode}，应该是RGBA")
        return False

def test_save_image_transparency():
    """测试保存功能是否保留透明通道"""
    print("\n测试图片保存透明通道保留...")
    
    # 创建一个带透明通道的测试图片
    test_image = Image.new('RGBA', (200, 200), (0, 255, 0, 128))  # 半透明绿色
    
    # 使用ImageProcessor保存
    processor = ImageProcessor()
    
    # 保存为PNG（应该保留透明通道）
    success = processor.save_image(test_image, 'test_save_png.png', 'PNG')
    
    if success:
        # 重新加载检查
        loaded = Image.open('test_save_png.png')
        if loaded.mode == 'RGBA':
            pixel = loaded.getpixel((100, 100))
            if pixel[3] < 255:  # 应该是半透明
                print(f"✓ PNG透明通道保留成功: 像素 = {pixel}")
                return True
            else:
                print(f"✗ PNG透明通道丢失: 像素 = {pixel}")
                return False
        else:
            print(f"✗ PNG模式错误: {loaded.mode}")
            return False
    else:
        print("✗ 保存PNG失败")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("透明通道保留功能测试")
    print("=" * 50)
    
    test1 = test_text_watermark_transparency()
    test2 = test_save_image_transparency()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("🎉 所有测试通过！透明通道功能正常工作")
        print("\n生成的测试文件:")
        print("  - test_original.png (原始透明图片)")
        print("  - test_watermarked.png (带水印的透明图片)")
        print("  - test_save_png.png (保存测试)")
    else:
        print("❌ 部分测试失败")
    print("=" * 50)

