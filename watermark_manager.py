"""
水印管理模块
处理文本水印和图片水印的创建、渲染和位置控制
"""

import math
from typing import Tuple, Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path


class WatermarkManager:
    """水印管理器"""
    
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
        """初始化水印管理器"""
        self.watermark_config = {
            'type': 'text',  # 'text' 或 'image'
            'text': 'Watermark',
            'font_family': 'Arial',
            'font_size': 24,
            'font_color': '#FFFFFF',
            'opacity': 80,
            'position': 'bottom_right',
            'rotation': 0,
            'image_path': '',
            'image_scale': 1.0,
            'shadow': False,
            'outline': False,
            'outline_color': '#000000',
            'outline_width': 2
        }
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新水印配置
        
        Args:
            config: 新的配置字典
        """
        self.watermark_config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前水印配置"""
        return self.watermark_config.copy()
    
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
            # 尝试加载字体
            import os
            import platform
            
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
                'Calibri': {'regular': 'calibri.ttf', 'bold': 'calibrib.ttf', 'italic': 'calibrii.ttf', 'bold_italic': 'calibriz.ttf'},
                'Georgia': {'regular': 'georgia.ttf', 'bold': 'georgiab.ttf', 'italic': 'georgiai.ttf', 'bold_italic': 'georgiaz.ttf'},
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
                if not hasattr(self, '_font_file_cache'):
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
                if font is None and hasattr(self, '_font_file_cache'):
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
            # 使用适中的边距确保文字完整显示
            base_margin = max(font_size // 20, 8)  # 根据字体大小动态调整边距，更紧凑
            extra_margin = outline_width + 3 if (shadow or outline) else 0
            margin = base_margin + extra_margin
            
            # 考虑旋转后的额外空间（减少旋转边距）
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
                # 绘制多层文本模拟粗体效果
                for offset_x in [-1, 0, 1]:
                    for offset_y in [-1, 0, 1]:
                        draw.text((text_x + offset_x, text_y + offset_y), text, font=font, fill=text_color_rgba)
            else:
                draw.text((text_x, text_y), text, font=font, fill=text_color_rgba)
            
            # 应用斜体效果（使用仿射变换）
            if need_simulate_italic:
                # 使用transform创建斜体效果
                watermark = watermark.transform(
                    watermark.size,
                    Image.AFFINE,
                    (1, 0.3, 0, 0, 1, 0),  # 仿射变换矩阵：水平倾斜
                    resample=Image.Resampling.BICUBIC
                )
            
            # 旋转水印
            if rotation != 0:
                watermark = watermark.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            
            return watermark
            
        except Exception as e:
            print(f"创建文本水印失败: {e}")
            # 返回一个简单的默认水印
            return self._create_default_watermark(text, font_size, color, opacity)
    
    def create_image_watermark(self, image_path: str, scale: float = 1.0, 
                             opacity: int = 80, rotation: float = 0) -> Optional[Image.Image]:
        """
        创建图片水印
        
        Args:
            image_path: 水印图片路径
            scale: 缩放比例
            opacity: 透明度 (0-100)
            rotation: 旋转角度
            
        Returns:
            PIL.Image: 图片水印，加载失败返回None
        """
        try:
            if not Path(image_path).exists():
                return None
            
            # 加载水印图片
            watermark = Image.open(image_path)
            
            # 确保图片有透明通道
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')
            
            # 调整透明度
            if opacity < 100:
                alpha = watermark.split()[-1]
                alpha = alpha.point(lambda p: int(p * opacity / 100))
                watermark.putalpha(alpha)
            
            # 缩放水印
            if scale != 1.0:
                new_size = (int(watermark.width * scale), int(watermark.height * scale))
                watermark = watermark.resize(new_size, Image.Resampling.LANCZOS)
            
            # 旋转水印
            if rotation != 0:
                watermark = watermark.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            
            return watermark
            
        except Exception as e:
            print(f"创建图片水印失败: {e}")
            return None
    
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
                x, y = self._calculate_position(result.size, watermark.size, position)
            
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
    
    def _calculate_position(self, image_size: Tuple[int, int], 
                          watermark_size: Tuple[int, int], 
                          position: str) -> Tuple[int, int]:
        """
        计算水印位置
        
        Args:
            image_size: 图片尺寸 (width, height)
            watermark_size: 水印尺寸 (width, height)
            position: 位置名称
            
        Returns:
            Tuple[int, int]: 水印位置坐标 (x, y)
        """
        img_width, img_height = image_size
        wm_width, wm_height = watermark_size
        
        if position in self.POSITIONS:
            rel_x, rel_y = self.POSITIONS[position]
            x = int((img_width - wm_width) * rel_x)
            y = int((img_height - wm_height) * rel_y)
        else:
            # 默认位置：右下角
            x = img_width - wm_width - 10
            y = img_height - wm_height - 10
        
        return x, y
    
    def _hex_to_rgba(self, hex_color: str, opacity: int) -> Tuple[int, int, int, int]:
        """
        将十六进制颜色转换为RGBA
        
        Args:
            hex_color: 十六进制颜色值 (如 '#FFFFFF')
            opacity: 透明度 (0-100)
            
        Returns:
            Tuple[int, int, int, int]: RGBA值
        """
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(255 * opacity / 100)
        return (r, g, b, a)
    
    def _create_default_watermark(self, text: str, font_size: int, 
                                color: str, opacity: int) -> Image.Image:
        """
        创建默认水印（当字体加载失败时使用）
        
        Args:
            text: 水印文本
            font_size: 字体大小
            color: 字体颜色
            opacity: 透明度
            
        Returns:
            PIL.Image: 默认水印图片
        """
        # 使用默认字体
        font = ImageFont.load_default()
        
        # 创建临时图片测量文本
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 创建水印图片
        watermark = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        # 绘制文本
        text_color_rgba = self._hex_to_rgba(color, opacity)
        draw.text((10, 10), text, font=font, fill=text_color_rgba)
        
        return watermark
    
    def _build_font_cache(self, fonts_dir: str):
        """
        构建字体文件缓存，映射字体名称到字体文件路径
        
        Args:
            fonts_dir: 字体目录路径
        """
        import os
        
        self._font_file_cache = {}
        font_files_found = 0
        
        try:
            # 遍历字体目录
            for font_file in os.listdir(fonts_dir):
                if font_file.lower().endswith(('.ttf', '.ttc', '.otf')):
                    font_path = os.path.join(fonts_dir, font_file)
                    font_files_found += 1
                    
                    # 使用文件名作为键（去除扩展名）
                    base_name = os.path.splitext(font_file)[0]
                    
                    # 添加多种可能的键值映射
                    keys_to_add = [
                        base_name.lower(),  # 全小写
                        base_name.lower().replace(' ', ''),  # 无空格
                        base_name.lower().replace(' ', '-'),  # 空格换成-
                        base_name.lower().replace(' ', '_'),  # 空格换成_
                        base_name.lower().replace('-', ''),  # 无-
                        base_name.lower().replace('_', ''),  # 无_
                    ]
                    
                    for key in keys_to_add:
                        if key and key not in self._font_file_cache:
                            self._font_file_cache[key] = font_path
            
            # 字体缓存构建完成（静默）
            pass
            
        except Exception as e:
            print(f"构建字体缓存失败: {e}")
            self._font_file_cache = {}
    
    def get_available_fonts(self) -> List[str]:
        """
        获取常用字体列表（经过测试确保可用）
        
        Returns:
            List[str]: 字体名称列表
        """
        # 返回常用且确保可用的字体
        return [
            '微软雅黑',
            '宋体', 
            '黑体',
            '楷体',
            'Arial',
            'Times New Roman',
            'Courier New',
            'Verdana'
        ]
    
    def preview_watermark(self, image: Image.Image) -> Image.Image:
        """
        预览水印效果
        
        Args:
            image: 原始图片
            
        Returns:
            PIL.Image: 带水印的预览图片
        """
        config = self.watermark_config
        
        if config['type'] == 'text':
            watermark = self.create_text_watermark(
                text=config['text'],
                font_family=config['font_family'],
                font_size=config['font_size'],
                color=config['font_color'],
                opacity=config['opacity'],
                rotation=config['rotation'],
                shadow=config.get('shadow', False),
                outline=config.get('outline', False),
                outline_color=config.get('outline_color', '#000000'),
                outline_width=config.get('outline_width', 2),
                bold=config.get('font_bold', False),
                italic=config.get('font_italic', False)
            )
        elif config['type'] == 'image' and config['image_path']:
            watermark = self.create_image_watermark(
                image_path=config['image_path'],
                scale=config['image_scale'],
                opacity=config['opacity'],
                rotation=config['rotation']
            )
        else:
            return image
        
        if watermark:
            return self.apply_watermark(image, watermark, config['position'])
        else:
            return image
    
    def preview_watermark_with_position(self, image: Image.Image, custom_position: tuple) -> Image.Image:
        """
        使用自定义位置预览水印效果
        
        Args:
            image: 原始图片
            custom_position: 自定义位置 (x, y)
            
        Returns:
            PIL.Image: 带水印的预览图片
        """
        config = self.watermark_config
        
        if config['type'] == 'text':
            watermark = self.create_text_watermark(
                text=config['text'],
                font_family=config['font_family'],
                font_size=config['font_size'],
                color=config['font_color'],
                opacity=config['opacity'],
                rotation=config['rotation'],
                shadow=config.get('shadow', False),
                outline=config.get('outline', False),
                outline_color=config.get('outline_color', '#000000'),
                outline_width=config.get('outline_width', 2),
                bold=config.get('font_bold', False),
                italic=config.get('font_italic', False)
            )
        elif config['type'] == 'image' and config['image_path']:
            watermark = self.create_image_watermark(
                image_path=config['image_path'],
                scale=config['image_scale'],
                opacity=config['opacity'],
                rotation=config['rotation']
            )
        else:
            return image
        
        if watermark:
            return self.apply_watermark(image, watermark, 'custom', custom_position)
        else:
            return image
