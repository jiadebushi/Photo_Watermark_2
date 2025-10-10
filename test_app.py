"""
Photo Watermark 2 - 测试脚本
用于验证各个模块是否正常工作
"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        from image_processor import ImageProcessor
        print("✓ ImageProcessor 导入成功")
    except Exception as e:
        print(f"✗ ImageProcessor 导入失败: {e}")
        return False
    
    try:
        from text_watermark_manager import TextWatermarkManager
        print("✓ TextWatermarkManager 导入成功")
    except Exception as e:
        print(f"✗ TextWatermarkManager 导入失败: {e}")
        return False
    
    try:
        from image_watermark_manager import ImageWatermarkManager
        print("✓ ImageWatermarkManager 导入成功")
    except Exception as e:
        print(f"✗ ImageWatermarkManager 导入失败: {e}")
        return False
    
    try:
        from config_manager import ConfigManager
        print("✓ ConfigManager 导入成功")
    except Exception as e:
        print(f"✗ ConfigManager 导入失败: {e}")
        return False
    
    return True

def test_image_processor():
    """测试图片处理器"""
    print("\n测试图片处理器...")
    
    try:
        from image_processor import ImageProcessor
        processor = ImageProcessor()
        
        # 测试支持的格式
        formats = processor.get_supported_extensions()
        print(f"✓ 支持的格式: {', '.join(formats)}")
        
        # 测试格式检查
        test_files = [
            "test.jpg",
            "test.png", 
            "test.bmp",
            "test.txt",
            "test.pdf"
        ]
        
        for file in test_files:
            is_supported = processor.is_supported_image(file)
            status = "✓" if is_supported else "✗"
            print(f"{status} {file}: {'支持' if is_supported else '不支持'}")
        
        return True
        
    except Exception as e:
        print(f"✗ ImageProcessor 测试失败: {e}")
        return False

def test_watermark_manager():
    """测试水印管理器（文本和图片）"""
    print("\n测试水印管理器...")
    
    try:
        from text_watermark_manager import TextWatermarkManager
        from image_watermark_manager import ImageWatermarkManager
        from PIL import Image
        
        # 测试文本水印管理器
        print("  - 测试文本水印管理器...")
        text_manager = TextWatermarkManager()
        test_image = Image.new('RGB', (400, 300), color='white')
        
        watermark = text_manager.create_text_watermark(
            text="Test Watermark",
            font_family="Arial",
            font_size=24,
            color="#FF0000",
            opacity=80
        )
        
        if watermark:
            print("    ✓ 文本水印创建成功")
        else:
            print("    ✗ 文本水印创建失败")
            return False
        
        # 测试水印应用
        result = text_manager.apply_watermark(test_image, watermark, "bottom_right")
        if result:
            print("    ✓ 文本水印应用成功")
        else:
            print("    ✗ 文本水印应用失败")
            return False
        
        # 测试字体列表
        fonts = text_manager.get_available_fonts()
        print(f"    ✓ 可用字体数量: {len(fonts)}")
        
        # 测试图片水印管理器
        print("  - 测试图片水印管理器...")
        image_manager = ImageWatermarkManager()
        
        # 测试位置计算
        img_shape = (300, 400)  # height, width
        wm_shape = (50, 100)    # height, width
        position = image_manager.calculate_position(img_shape, wm_shape, "bottom_right")
        if position:
            print(f"    ✓ 位置计算成功: {position}")
        else:
            print("    ✗ 位置计算失败")
            return False
        
        print("✓ 水印管理器测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 水印管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n测试配置管理器...")
    
    try:
        from config_manager import ConfigManager
        manager = ConfigManager("test_config")
        
        # 测试设置保存和加载
        manager.set_setting("test_key", "test_value")
        value = manager.get_setting("test_key")
        
        if value == "test_value":
            print("✓ 设置保存和加载成功")
        else:
            print("✗ 设置保存和加载失败")
            return False
        
        # 测试模板保存和加载
        test_template = {
            "type": "text",
            "text": "Test Template",
            "font_size": 20
        }
        
        if manager.save_template("test_template", test_template):
            print("✓ 模板保存成功")
        else:
            print("✗ 模板保存失败")
            return False
        
        loaded_template = manager.load_template("test_template")
        if loaded_template and loaded_template["text"] == "Test Template":
            print("✓ 模板加载成功")
        else:
            print("✗ 模板加载失败")
            return False
        
        # 清理测试文件
        manager.delete_template("test_template")
        
        return True
        
    except Exception as e:
        print(f"✗ ConfigManager 测试失败: {e}")
        return False

def test_dependencies():
    """测试依赖库"""
    print("\n测试依赖库...")
    
    required_modules = [
        ("tkinter", "GUI框架"),
        ("PIL", "图像处理库"),
        ("json", "JSON处理"),
        ("pathlib", "路径处理"),
        ("threading", "多线程支持")
    ]
    
    all_ok = True
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name} ({description})")
        except ImportError:
            print(f"✗ {module_name} ({description}) - 未安装")
            all_ok = False
    
    return all_ok

def cleanup_test_files():
    """清理测试文件"""
    print("\n清理测试文件...")
    
    test_config_dir = Path("test_config")
    if test_config_dir.exists():
        import shutil
        shutil.rmtree(test_config_dir)
        print("✓ 测试配置文件夹已清理")

def main():
    """主测试函数"""
    print("Photo Watermark 2 - 模块测试")
    print("=" * 40)
    
    tests = [
        ("依赖库检查", test_dependencies),
        ("模块导入测试", test_imports),
        ("图片处理器测试", test_image_processor),
        ("水印管理器测试", test_watermark_manager),
        ("配置管理器测试", test_config_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
        except Exception as e:
            print(f"✗ {test_name} 异常: {e}")
    
    # 清理测试文件
    cleanup_test_files()
    
    # 显示测试结果
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！程序可以正常运行。")
        print("\n运行程序:")
        print("python main.py")
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return False
    
    return True

if __name__ == "__main__":
    main()
