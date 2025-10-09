"""
文本水印管理模块
使用PIL处理文本水印的创建、渲染和位置控制
"""

import math
import os
import platform
from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


class TextWatermarkManager:
    """文本水印管理器（基于PIL）"""
    
    # 九宫格位置定义
    POSITIONS = {
        'top_left': (0.05, 0.05),
        'top_center': (0.5, 0.05),
        'top_right': (0.95, 0.05),
        'center_left': (0.05, 0.5),
        'center': (0.5, 0.5),
        'center_right': (0.95, 0.5),
        'bottom_left': (0.05, 0.95),
        'bottom_center': (0.5, 0.95),
        'bottom_right': (0.95, 0.95)
    }
    
    def __init__(self):
        """初始化文本水印管理器"""
        self._font_file_cache = None
    
    def _build_font_cache(self, fonts_dir: str) -> None:
        """
        构建字体文件缓存
        
        Args:
            fonts_dir: 字体目录路径
        """
        if self._font_file_cache is not None:
            return
        
        self._font_file_cache = {}
        
        try:
            for font_file in os.listdir(fonts_dir):
                if font_file.lower().endswith(('.ttf', '.ttc', '.otf')):
                    font_path = os.path.join(fonts_dir, font_file)
                    # 去掉扩展名和变体后缀
                    base_name = font_file.rsplit('.', 1)[0].lower()
                    
                    # 添加多种可能的键
                    self._font_file_cache[base_name] = font_path
                    self._font_file_cache[base_name.replace('-', '')] = font_path
                    self._font_file_cache[base_name.replace('_', '')] = font_path
                    self._font_file_cache[base_name.replace(' ', '')] = font_path
        except Exception as e:
            print(f"构建字体缓存时出错: {e}")
    
    def _hex_to_rgba(self, hex_color: str, opacity: int) -> Tuple[int, int, int, int]:
        """
        将十六进制颜色转换为RGBA
        
        Args:
            hex_color: 十六进制颜色字符串
            opacity: 透明度 (0-100)
            
        Returns:
            tuple: (R, G, B, A)
        """
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        a = int(255 * opacity / 100)
        return (r, g, b, a)
    
    def _create_default_watermark(self, text: str, font_size: int, 
                                  color: str, opacity: int) -> Image.Image:
        """
        创建默认水印（当字体加载失败时）
        
        Args:
            text: 水印文本
            font_size: 字体大小
            color: 字体颜色
            opacity: 透明度
            
        Returns:
            PIL.Image: 默认水印图片
        """
        font = ImageFont.load_default()
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        
        width = bbox[2] - bbox[0] + 20
        height = bbox[3] - bbox[1] + 20
        
        watermark = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        text_color_rgba = self._hex_to_rgba(color, opacity)
        draw.text((10, 10), text, font=font, fill=text_color_rgba)
        
        return watermark
    
    def create_text_watermark(self, text: str, font_family: str, font_size: int,
                            color: str, opacity: int, rotation: float = 0,
                            shadow: bool = False, outline: bool = False,
                            outline_color: str = '#000000', outline_width: int = 2,
                            bold: bool = False, italic: bool = False) -> Image.Image:
        """
        创建文本水印
        
        Args:
            text: 水印文本
            font_family: 字体名称
            font_size: 字体大小
            color: 字体颜色
            opacity: 透明度 (0-100)
            rotation: 旋转角度
            shadow: 是否添加阴影
            outline: 是否添加描边
            outline_color: 描边颜色
            outline_width: 描边宽度
            bold: 是否粗体
            italic: 是否斜体
            
        Returns:
            PIL.Image: 文本水印图片
        """
        try:
            font = None
            
            # Windows常用字体路径映射（包括粗体、斜体变体）
            windows_fonts = {
                '微软雅黑': {'regular': 'msyh.ttc', 'bold': 'msyhbd.ttc'},
                'Microsoft YaHei': {'regular': 'msyh.ttc', 'bold': 'msyhbd.ttc'},
                '宋体': {'regular': 'simsun.ttc', 'bold': 'simsun.ttc'},
                'SimSun': {'regular': 'simsun.ttc', 'bold': 'simsun.ttc'},
                '黑体': {'regular': 'simhei.ttf', 'bold': 'simhei.ttf'},
                'SimHei': {'regular': 'simhei.ttf', 'bold': 'simhei.ttf'},
                '楷体': {'regular': 'simkai.ttf', 'bold': 'simkai.ttf'},
                'KaiTi': {'regular': 'simkai.ttf', 'bold': 'simkai.ttf'},
                'Arial': {'regular': 'arial.ttf', 'bold': 'arialbd.ttf', 'italic': 'ariali.ttf', 'bold_italic': 'arialbi.ttf'},
                'Times New Roman': {'regular': 'times.ttf', 'bold': 'timesbd.ttf', 'italic': 'timesi.ttf', 'bold_italic': 'timesbi.ttf'},
                'Courier New': {'regular': 'cour.ttf', 'bold': 'courbd.ttf', 'italic': 'couri.ttf', 'bold_italic': 'courbi.ttf'},
                'Verdana': {'regular': 'verdana.ttf', 'bold': 'verdanab.ttf', 'italic': 'verdanai.ttf', 'bold_italic': 'verdanaz.ttf'},
            }
            
            # 确定要使用的字体变体
            font_variant = 'regular'
            if bold and italic:
                font_variant = 'bold_italic'
            elif bold:
                font_variant = 'bold'
            elif italic:
                font_variant = 'italic'
            
            # Windows字体目录
            if platform.system() == 'Windows':
                fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
                
                # 建立字体文件索引（首次调用时）
                if self._font_file_cache is None:
                    self._build_font_cache(fonts_dir)
                
                # 1. 尝试从预定义映射加载
                if font_family in windows_fonts:
                    font_info = windows_fonts[font_family]
                    font_file = font_info.get(font_variant) or font_info.get('regular')
                    font_path = os.path.join(fonts_dir, font_file)
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                    except (OSError, IOError):
                        pass
                
                # 2. 从缓存中搜索
                if font is None and self._font_file_cache:
                    search_names = [
                        font_family.lower(),
                        font_family.lower().replace(' ', ''),
                        font_family.lower().replace(' ', '-'),
                        font_family.lower().replace(' ', '_'),
                    ]
                    
                    for search_name in search_names:
                        if search_name in self._font_file_cache:
                            font_path = self._font_file_cache[search_name]
                            try:
                                font = ImageFont.truetype(font_path, font_size)
                                break
                            except (OSError, IOError):
                                continue
                
                # 3. 如果还没成功，使用默认字体
                if font is None:
                    for default_font in ['msyh.ttc', 'simsun.ttc', 'simhei.ttf', 'arial.ttf']:
                        try:
                            font = ImageFont.truetype(os.path.join(fonts_dir, default_font), font_size)
                            break
                        except (OSError, IOError):
                            continue
            else:
                # 非Windows系统，尝试直接加载
                try:
                    font = ImageFont.truetype(font_family, font_size)
                except (OSError, IOError):
                    pass
            
            # 如果所有方法都失败，使用默认字体
            if font is None:
                font = ImageFont.load_default()
            
            # 记录是否需要模拟粗体/斜体（用于中文字体）
            need_simulate_bold = bold
            need_simulate_italic = italic
            
            # 如果成功加载了带bold/italic的字体变体，则不需要模拟
            if font_variant != 'regular' and font is not None:
                # 检查是否真的加载了变体字体文件
                if platform.system() == 'Windows' and font_family in windows_fonts:
                    font_info = windows_fonts[font_family]
                    if font_variant in font_info:
                        need_simulate_bold = False
                        need_simulate_italic = False
            
            # 创建临时图片来测量文本尺寸
            temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # 获取文本边界框
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 添加边距和阴影/描边空间
            base_margin = max(font_size // 20, 8)
            extra_margin = outline_width + 3 if (shadow or outline) else 0
            margin = base_margin + extra_margin
            
            # 考虑旋转后的额外空间
            rotation_margin = int(max(text_width, text_height) * 0.1) if rotation != 0 else 0
            margin = margin + rotation_margin
            
            img_width = text_width + margin * 2
            img_height = text_height + margin * 2
            
            # 创建水印图片
            watermark = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # 计算文本位置（居中）
            text_x = margin
            text_y = margin
            
            # 添加阴影
            if shadow:
                shadow_offset = 2
                shadow_color = (0, 0, 0, int(255 * opacity / 100 * 0.5))
                draw.text((text_x + shadow_offset, text_y + shadow_offset), 
                         text, font=font, fill=shadow_color)
            
            # 添加描边
            if outline and outline_width > 0:
                outline_color_rgba = self._hex_to_rgba(outline_color, opacity)
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx*dx + dy*dy <= outline_width*outline_width:
                            draw.text((text_x + dx, text_y + dy), text, font=font, fill=outline_color_rgba)
            
            # 绘制主文本
            text_color_rgba = self._hex_to_rgba(color, opacity)
            
            # 如果需要模拟粗体（用于中文字体）
            if need_simulate_bold:
                for offset_x in [-1, 0, 1]:
                    for offset_y in [-1, 0, 1]:
                        draw.text((text_x + offset_x, text_y + offset_y), text, font=font, fill=text_color_rgba)
            else:
                draw.text((text_x, text_y), text, font=font, fill=text_color_rgba)
            
            # 应用斜体效果（使用仿射变换）
            if need_simulate_italic:
                watermark = watermark.transform(
                    watermark.size,
                    Image.AFFINE,
                    (1, 0.3, 0, 0, 1, 0),
                    resample=Image.Resampling.BICUBIC
                )
            
            # 旋转水印
            if rotation != 0:
                watermark = watermark.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            
            return watermark
            
        except Exception as e:
            print(f"创建文本水印失败: {e}")
            return self._create_default_watermark(text, font_size, color, opacity)
    
    def calculate_position(self, image_size: Tuple[int, int], 
                          watermark_size: Tuple[int, int],
                          position: str) -> Tuple[int, int]:
        """
        计算水印在图片上的位置
        
        Args:
            image_size: 原始图片尺寸 (width, height)
            watermark_size: 水印尺寸 (width, height)
            position: 位置名称
            
        Returns:
            tuple: (x, y) 坐标
        """
        img_w, img_h = image_size
        wm_w, wm_h = watermark_size
        
        if position not in self.POSITIONS:
            position = 'bottom_right'
        
        ratio_x, ratio_y = self.POSITIONS[position]
        
        # 计算位置
        x = int((img_w - wm_w) * ratio_x)
        y = int((img_h - wm_h) * ratio_y)
        
        # 确保水印在图片边界内
        x = max(0, min(x, img_w - wm_w))
        y = max(0, min(y, img_h - wm_h))
        
        return x, y
    
    def apply_watermark(self, image: Image.Image, watermark: Image.Image, 
                       position: str, custom_position: Optional[Tuple[int, int]] = None) -> Image.Image:
        """
        将水印应用到图片上
        
        Args:
            image: 原始图片
            watermark: 水印图片
            position: 位置名称或'custom'
            custom_position: 自定义位置坐标 (x, y)
            
        Returns:
            PIL.Image: 带水印的图片
        """
        try:
            # 创建图片副本
            result = image.copy()
            
            # 确保图片有透明通道
            if result.mode != 'RGBA':
                result = result.convert('RGBA')
            
            # 计算水印位置
            if position == 'custom' and custom_position:
                x, y = custom_position
            else:
                x, y = self.calculate_position(result.size, watermark.size, position)
            
            # 确保水印在图片范围内
            x = max(0, min(x, result.width - watermark.width))
            y = max(0, min(y, result.height - watermark.height))
            
            # 将水印合成到图片上
            if watermark.mode == 'RGBA':
                result.paste(watermark, (x, y), watermark)
            else:
                result.paste(watermark, (x, y))
            
            return result
            
        except Exception as e:
            print(f"应用水印失败: {e}")
            return image
    
    def preview_watermark(self, image_input, text: str, font_family: str,
                         font_size: int, color: str, opacity: int,
                         position: str, rotation: float = 0,
                         shadow: bool = False, outline: bool = False,
                         outline_color: str = '#000000', outline_width: int = 2,
                         bold: bool = False, italic: bool = False,
                         max_preview_size: Tuple[int, int] = (800, 600)) -> Optional[Image.Image]:
        """
        生成水印预览图
        
        Args:
            image_input: 原始图片路径(str)或PIL Image对象
            text: 水印文本
            font_family: 字体名称
            font_size: 字体大小
            color: 字体颜色
            opacity: 透明度
            position: 水印位置
            rotation: 旋转角度
            shadow: 是否添加阴影
            outline: 是否添加描边
            outline_color: 描边颜色
            outline_width: 描边宽度
            bold: 是否粗体
            italic: 是否斜体
            max_preview_size: 预览图最大尺寸
            
        Returns:
            PIL.Image: 预览图，失败返回None
        """
        try:
            # 加载图片
            if isinstance(image_input, str):
                image = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                image = image_input
            else:
                print(f"不支持的图片输入类型: {type(image_input)}")
                return None
            
            # 创建文本水印
            watermark = self.create_text_watermark(
                text, font_family, font_size, color, opacity,
                rotation, shadow, outline, outline_color, outline_width,
                bold, italic
            )
            
            # 应用水印
            result = self.apply_watermark(image, watermark, position)
            
            # 调整预览图大小
            if result.mode == 'RGBA':
                result = result.convert('RGB')
            
            w, h = result.size
            max_w, max_h = max_preview_size
            
            if w > max_w or h > max_h:
                scale = min(max_w / w, max_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                result = result.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            return result
            
        except Exception as e:
            print(f"生成预览图时出错: {e}")
            return None
    
    def preview_watermark_with_position(self, image_input, text: str,
                                       font_family: str, font_size: int,
                                       color: str, opacity: int,
                                       rotation: float = 0,
                                       shadow: bool = False, outline: bool = False,
                                       outline_color: str = '#000000',
                                       outline_width: int = 2,
                                       bold: bool = False, italic: bool = False,
                                       custom_position: Optional[Tuple[int, int]] = None,
                                       max_preview_size: Tuple[int, int] = (800, 600)) -> Optional[Image.Image]:
        """
        使用自定义位置生成水印预览图
        
        Args:
            image_input: 原始图片路径(str)或PIL Image对象
            text: 水印文本
            font_family: 字体名称
            font_size: 字体大小
            color: 字体颜色
            opacity: 透明度
            rotation: 旋转角度
            shadow: 是否添加阴影
            outline: 是否添加描边
            outline_color: 描边颜色
            outline_width: 描边宽度
            bold: 是否粗体
            italic: 是否斜体
            custom_position: 自定义位置 (x, y)
            max_preview_size: 预览图最大尺寸
            
        Returns:
            PIL.Image: 预览图，失败返回None
        """
        try:
            # 加载图片
            if isinstance(image_input, str):
                image = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                image = image_input
            else:
                print(f"不支持的图片输入类型: {type(image_input)}")
                return None
            
            # 创建文本水印
            watermark = self.create_text_watermark(
                text, font_family, font_size, color, opacity,
                rotation, shadow, outline, outline_color, outline_width,
                bold, italic
            )
            
            # 应用水印
            result = self.apply_watermark(image, watermark, 'custom', custom_position)
            
            # 调整预览图大小
            if result.mode == 'RGBA':
                result = result.convert('RGB')
            
            w, h = result.size
            max_w, max_h = max_preview_size
            
            if w > max_w or h > max_h:
                scale = min(max_w / w, max_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                result = result.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            return result
            
        except Exception as e:
            print(f"生成预览图时出错: {e}")
            return None
    
    @staticmethod
    def get_available_fonts() -> List[str]:
        """
        获取可用的系统字体列表
        
        Returns:
            list: 字体名称列表
        """
        # 返回经过测试的常用字体
        return [
            'Arial',
            'Times New Roman',
            'Courier New',
            'Verdana',
            '微软雅黑',
            '宋体',
            '黑体',
            '楷体'
        ]

