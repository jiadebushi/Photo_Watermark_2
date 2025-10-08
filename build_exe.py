"""
Windows可执行文件构建脚本
使用PyInstaller将Python应用程序打包为Windows可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def build_executable():
    """构建可执行文件"""
    print("开始构建Photo Watermark 2可执行文件...")
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: PyInstaller未安装，请先运行: pip install pyinstaller")
        return False
    
    # 构建参数
    build_args = [
        "pyinstaller",
        "--onefile",                    # 打包为单个文件
        "--windowed",                   # 无控制台窗口（GUI应用）
        "--name=PhotoWatermark2",       # 可执行文件名
        "--icon=icon.ico",              # 图标文件（如果存在）
        "--add-data=config;config",     # 包含配置文件夹
        "--hidden-import=PIL._tkinter_finder",  # 确保PIL的tkinter支持被包含
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.colorchooser",
        "--clean",                      # 清理临时文件
        "main.py"                       # 主程序文件
    ]
    
    # 如果没有图标文件，移除图标参数
    if not Path("icon.ico").exists():
        build_args = [arg for arg in build_args if not arg.startswith("--icon")]
        print("未找到icon.ico文件，将使用默认图标")
    
    # 如果没有config文件夹，移除相关参数
    if not Path("config").exists():
        build_args = [arg for arg in build_args if not arg.startswith("--add-data")]
        print("未找到config文件夹，将使用默认配置")
    
    try:
        # 执行构建命令
        print("执行构建命令...")
        print(" ".join(build_args))
        result = subprocess.run(build_args, check=True, capture_output=True, text=True)
        
        print("构建成功！")
        print("可执行文件位置: dist/PhotoWatermark2.exe")
        
        # 检查生成的文件
        exe_path = Path("dist/PhotoWatermark2.exe")
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"文件大小: {file_size:.1f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"构建过程中发生错误: {e}")
        return False


def create_portable_version():
    """创建便携版本"""
    print("\n创建便携版本...")
    
    # 创建便携版本文件夹
    portable_dir = Path("PhotoWatermark2_Portable")
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    portable_dir.mkdir()
    
    # 复制可执行文件
    exe_path = Path("dist/PhotoWatermark2.exe")
    if exe_path.exists():
        shutil.copy2(exe_path, portable_dir / "PhotoWatermark2.exe")
        print(f"可执行文件已复制到: {portable_dir}")
    
    # 创建配置文件夹
    config_dir = portable_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # 创建README文件
    readme_content = """# Photo Watermark 2 便携版

## 使用方法
1. 双击 PhotoWatermark2.exe 启动程序
2. 点击"选择图片"或"选择文件夹"导入图片
3. 在右侧面板设置水印参数
4. 点击"批量导出"或"导出当前"保存带水印的图片

## 功能特点
- 支持文本水印和图片水印
- 支持多种图片格式 (JPEG, PNG, BMP, TIFF)
- 九宫格位置定位 + 手动拖拽
- 水印模板保存和加载
- 批量处理功能

## 注意事项
- 首次运行会在当前目录创建config文件夹保存配置
- 支持透明PNG图片作为水印
- 建议输出文件夹与原图片文件夹不同，避免覆盖原图

## 系统要求
- Windows 10/11
- 无需安装Python或其他依赖

如有问题，请检查config文件夹中的日志文件。
"""
    
    with open(portable_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print(f"便携版本创建完成: {portable_dir}")


def cleanup_build_files():
    """清理构建临时文件"""
    print("\n清理构建临时文件...")
    
    # 删除构建过程中生成的临时文件夹
    temp_dirs = ["build", "__pycache__"]
    for temp_dir in temp_dirs:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
            print(f"已删除: {temp_dir}")
    
    # 删除.spec文件
    spec_files = list(Path(".").glob("*.spec"))
    for spec_file in spec_files:
        spec_file.unlink()
        print(f"已删除: {spec_file}")


def main():
    """主函数"""
    print("Photo Watermark 2 - Windows可执行文件构建工具")
    print("=" * 50)
    
    # 检查必要文件是否存在
    required_files = ["main.py", "image_processor.py", "watermark_manager.py", "config_manager.py"]
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"错误: 缺少必要文件: {', '.join(missing_files)}")
        return
    
    # 构建可执行文件
    if build_executable():
        # 创建便携版本
        create_portable_version()
        
        # 清理临时文件
        cleanup_build_files()
        
        print("\n构建完成！")
        print("可执行文件: dist/PhotoWatermark2.exe")
        print("便携版本: PhotoWatermark2_Portable/")
        print("\n使用方法:")
        print("1. 直接运行 dist/PhotoWatermark2.exe")
        print("2. 或者使用便携版本 PhotoWatermark2_Portable/PhotoWatermark2.exe")
    else:
        print("\n构建失败，请检查错误信息")


if __name__ == "__main__":
    main()
