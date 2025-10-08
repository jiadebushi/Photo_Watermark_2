"""
图片处理模块
处理图片导入、导出、格式转换、尺寸调整等功能
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageOps
import tkinter as tk
from tkinter import filedialog, messagebox


class ImageProcessor:
    """图片处理器"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {
        'JPEG': ['.jpg', '.jpeg'],
        'PNG': ['.png'],
        'BMP': ['.bmp'],
        'TIFF': ['.tiff', '.tif']
    }
    
    def __init__(self):
        """初始化图片处理器"""
        self.images: List[Dict[str, Any]] = []
        self.current_image_index = 0
    
    def get_supported_extensions(self) -> List[str]:
        """获取所有支持的图片扩展名"""
        extensions = []
        for format_exts in self.SUPPORTED_FORMATS.values():
            extensions.extend(format_exts)
        return extensions
    
    def is_supported_image(self, file_path: str) -> bool:
        """
        检查文件是否为支持的图片格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为支持的图片格式
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.get_supported_extensions()
    
    def load_image(self, file_path: str) -> Optional[Image.Image]:
        """
        加载图片文件
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            PIL.Image: 图片对象，加载失败返回None
        """
        try:
            image = Image.open(file_path)
            # 确保图片是RGB模式（除了PNG透明图片）
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            return image
        except Exception as e:
            print(f"加载图片失败: {file_path}, 错误: {e}")
            return None
    
    def add_image(self, file_path: str) -> bool:
        """
        添加图片到处理列表
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            bool: 添加是否成功
        """
        if not self.is_supported_image(file_path):
            return False
        
        image = self.load_image(file_path)
        if image is None:
            return False
        
        # 生成缩略图
        thumbnail = self.create_thumbnail(image, (150, 150))
        
        image_info = {
            'file_path': file_path,
            'filename': Path(file_path).name,
            'image': image,
            'thumbnail': thumbnail,
            'original_size': image.size,
            'format': image.format or 'Unknown'
        }
        
        self.images.append(image_info)
        return True
    
    def add_images_from_folder(self, folder_path: str) -> int:
        """
        从文件夹批量添加图片
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            int: 成功添加的图片数量
        """
        added_count = 0
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            return 0
        
        for file_path in folder.iterdir():
            if file_path.is_file() and self.is_supported_image(str(file_path)):
                if self.add_image(str(file_path)):
                    added_count += 1
        
        return added_count
    
    def create_thumbnail(self, image: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """
        创建缩略图
        
        Args:
            image: 原始图片
            size: 缩略图尺寸 (width, height)
            
        Returns:
            PIL.Image: 缩略图
        """
        return image.copy().thumbnail(size, Image.Resampling.LANCZOS)
    
    def get_current_image(self) -> Optional[Image.Image]:
        """获取当前选中的图片"""
        if 0 <= self.current_image_index < len(self.images):
            return self.images[self.current_image_index]['image']
        return None
    
    def get_current_image_info(self) -> Optional[Dict[str, Any]]:
        """获取当前图片信息"""
        if 0 <= self.current_image_index < len(self.images):
            return self.images[self.current_image_index]
        return None
    
    def set_current_image(self, index: int) -> bool:
        """
        设置当前图片
        
        Args:
            index: 图片索引
            
        Returns:
            bool: 设置是否成功
        """
        if 0 <= index < len(self.images):
            self.current_image_index = index
            return True
        return False
    
    def get_image_list(self) -> List[Dict[str, Any]]:
        """获取图片列表"""
        return self.images.copy()
    
    def clear_images(self) -> None:
        """清空图片列表"""
        self.images.clear()
        self.current_image_index = 0
    
    def remove_image(self, index: int) -> bool:
        """
        移除指定索引的图片
        
        Args:
            index: 图片索引
            
        Returns:
            bool: 移除是否成功
        """
        if 0 <= index < len(self.images):
            del self.images[index]
            if self.current_image_index >= len(self.images):
                self.current_image_index = max(0, len(self.images) - 1)
            return True
        return False
    
    def resize_image(self, image: Image.Image, size: Tuple[int, int], 
                    method: str = 'resize') -> Image.Image:
        """
        调整图片尺寸
        
        Args:
            image: 原始图片
            size: 目标尺寸 (width, height)
            method: 调整方法 ('resize', 'thumbnail', 'crop')
            
        Returns:
            PIL.Image: 调整后的图片
        """
        if method == 'resize':
            return image.resize(size, Image.Resampling.LANCZOS)
        elif method == 'thumbnail':
            resized = image.copy()
            resized.thumbnail(size, Image.Resampling.LANCZOS)
            return resized
        elif method == 'crop':
            return ImageOps.fit(image, size, Image.Resampling.LANCZOS)
        else:
            return image.resize(size, Image.Resampling.LANCZOS)
    
    def save_image(self, image: Image.Image, output_path: str, 
                  format: str = 'JPEG', quality: int = 95) -> bool:
        """
        保存图片
        
        Args:
            image: 要保存的图片
            output_path: 输出路径
            format: 输出格式
            quality: JPEG质量 (1-100)
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 根据格式调整图片模式
            if format == 'JPEG' and image.mode in ('RGBA', 'LA'):
                # JPEG不支持透明通道，转换为RGB
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
                image = background
            elif format == 'PNG' and image.mode == 'RGB':
                # PNG支持透明通道，保持原样
                pass
            
            # 保存图片
            save_kwargs = {}
            if format == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            
            image.save(output_path, format=format, **save_kwargs)
            return True
            
        except Exception as e:
            print(f"保存图片失败: {output_path}, 错误: {e}")
            return False
    
    def batch_export(self, output_folder: str, naming_rule: str = 'original',
                    prefix: str = '', suffix: str = '', 
                    output_format: str = 'JPEG', quality: int = 95) -> Dict[str, Any]:
        """
        批量导出图片
        
        Args:
            output_folder: 输出文件夹
            naming_rule: 命名规则 ('original', 'prefix', 'suffix')
            prefix: 文件名前缀
            suffix: 文件名后缀
            output_format: 输出格式
            quality: JPEG质量
            
        Returns:
            Dict: 导出结果统计
        """
        results = {
            'success_count': 0,
            'failed_count': 0,
            'failed_files': []
        }
        
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, image_info in enumerate(self.images):
            try:
                # 生成输出文件名
                original_name = Path(image_info['file_path']).stem
                original_ext = Path(image_info['file_path']).suffix
                
                if naming_rule == 'prefix':
                    new_name = f"{prefix}{original_name}{original_ext}"
                elif naming_rule == 'suffix':
                    new_name = f"{original_name}{suffix}{original_ext}"
                else:  # original
                    new_name = f"{original_name}{original_ext}"
                
                # 确保输出格式扩展名正确
                if output_format == 'JPEG' and not new_name.lower().endswith(('.jpg', '.jpeg')):
                    new_name = f"{Path(new_name).stem}.jpg"
                elif output_format == 'PNG' and not new_name.lower().endswith('.png'):
                    new_name = f"{Path(new_name).stem}.png"
                
                output_file_path = output_path / new_name
                
                # 保存图片
                if self.save_image(image_info['image'], str(output_file_path), output_format, quality):
                    results['success_count'] += 1
                else:
                    results['failed_count'] += 1
                    results['failed_files'].append(image_info['filename'])
                    
            except Exception as e:
                results['failed_count'] += 1
                results['failed_files'].append(image_info['filename'])
                print(f"导出图片失败: {image_info['filename']}, 错误: {e}")
        
        return results
    
    def select_images(self, parent_window=None) -> List[str]:
        """
        打开文件选择对话框选择图片
        
        Args:
            parent_window: 父窗口
            
        Returns:
            List[str]: 选择的文件路径列表
        """
        file_types = [
            ("图片文件", " ".join([f"*{ext}" for ext in self.get_supported_extensions()])),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("PNG文件", "*.png"),
            ("BMP文件", "*.bmp"),
            ("TIFF文件", "*.tiff *.tif"),
            ("所有文件", "*.*")
        ]
        
        file_paths = filedialog.askopenfilenames(
            parent=parent_window,
            title="选择图片文件",
            filetypes=file_types
        )
        
        return list(file_paths)
    
    def select_folder(self, parent_window=None) -> Optional[str]:
        """
        打开文件夹选择对话框
        
        Args:
            parent_window: 父窗口
            
        Returns:
            str: 选择的文件夹路径，取消选择返回None
        """
        folder_path = filedialog.askdirectory(
            parent=parent_window,
            title="选择图片文件夹"
        )
        
        return folder_path if folder_path else None
