"""
图片水印管理模块
使用OpenCV处理图片水印的创建、渲染和位置控制
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from pathlib import Path


class ImageWatermarkManager:
    """图片水印管理器（基于OpenCV）"""
    
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
        """初始化图片水印管理器"""
        self.watermark_cache = {}
    
    def load_watermark_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        加载水印图片
        
        Args:
            image_path: 水印图片路径
            
        Returns:
            numpy.ndarray: 水印图片（BGRA格式），如果加载失败返回None
        """
        try:
            if not Path(image_path).exists():
                print(f"水印图片不存在: {image_path}")
                return None
            
            # 使用OpenCV加载图片，保留Alpha通道
            watermark = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            
            if watermark is None:
                print(f"无法加载水印图片: {image_path}")
                return None
            
            # 如果图片没有Alpha通道，添加一个不透明的Alpha通道
            if watermark.shape[2] == 3:
                # BGR转BGRA
                alpha = np.ones((watermark.shape[0], watermark.shape[1], 1), dtype=watermark.dtype) * 255
                watermark = np.concatenate([watermark, alpha], axis=2)
            
            return watermark
            
        except Exception as e:
            print(f"加载水印图片时出错: {e}")
            return None
    
    def resize_watermark(self, watermark: np.ndarray, scale: float, 
                        max_width: Optional[int] = None, 
                        max_height: Optional[int] = None) -> np.ndarray:
        """
        调整水印图片大小
        
        Args:
            watermark: 原始水印图片
            scale: 缩放比例（0.1-10.0）
            max_width: 最大宽度限制
            max_height: 最大高度限制
            
        Returns:
            numpy.ndarray: 调整大小后的水印图片
        """
        try:
            h, w = watermark.shape[:2]
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # 应用最大尺寸限制
            if max_width and new_w > max_width:
                ratio = max_width / new_w
                new_w = max_width
                new_h = int(new_h * ratio)
            
            if max_height and new_h > max_height:
                ratio = max_height / new_h
                new_h = max_height
                new_w = int(new_w * ratio)
            
            # 确保尺寸至少为1
            new_w = max(1, new_w)
            new_h = max(1, new_h)
            
            # 使用高质量插值方法调整大小
            resized = cv2.resize(watermark, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            return resized
            
        except Exception as e:
            print(f"调整水印大小时出错: {e}")
            return watermark
    
    def apply_opacity(self, watermark: np.ndarray, opacity: int) -> np.ndarray:
        """
        调整水印透明度
        
        Args:
            watermark: 水印图片（BGRA格式）
            opacity: 透明度（0-100）
            
        Returns:
            numpy.ndarray: 调整透明度后的水印图片
        """
        try:
            # 复制水印以避免修改原始数据
            watermark_copy = watermark.copy()
            
            # 调整Alpha通道
            alpha_scale = opacity / 100.0
            watermark_copy[:, :, 3] = (watermark_copy[:, :, 3] * alpha_scale).astype(np.uint8)
            
            return watermark_copy
            
        except Exception as e:
            print(f"调整水印透明度时出错: {e}")
            return watermark
    
    def rotate_watermark(self, watermark: np.ndarray, angle: float) -> np.ndarray:
        """
        旋转水印图片
        
        Args:
            watermark: 水印图片
            angle: 旋转角度（度）
            
        Returns:
            numpy.ndarray: 旋转后的水印图片
        """
        try:
            if angle == 0:
                return watermark
            
            h, w = watermark.shape[:2]
            center = (w // 2, h // 2)
            
            # 计算旋转矩阵
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # 计算旋转后的边界框
            cos = np.abs(rotation_matrix[0, 0])
            sin = np.abs(rotation_matrix[0, 1])
            new_w = int((h * sin) + (w * cos))
            new_h = int((h * cos) + (w * sin))
            
            # 调整旋转矩阵以考虑平移
            rotation_matrix[0, 2] += (new_w / 2) - center[0]
            rotation_matrix[1, 2] += (new_h / 2) - center[1]
            
            # 执行旋转，使用透明背景
            rotated = cv2.warpAffine(watermark, rotation_matrix, (new_w, new_h),
                                    flags=cv2.INTER_LANCZOS4,
                                    borderMode=cv2.BORDER_CONSTANT,
                                    borderValue=(0, 0, 0, 0))
            
            return rotated
            
        except Exception as e:
            print(f"旋转水印时出错: {e}")
            return watermark
    
    def calculate_position(self, image_shape: Tuple[int, int], 
                          watermark_shape: Tuple[int, int],
                          position: str) -> Tuple[int, int]:
        """
        计算水印在图片上的位置
        
        Args:
            image_shape: 原始图片尺寸 (height, width)
            watermark_shape: 水印尺寸 (height, width)
            position: 位置名称
            
        Returns:
            tuple: (x, y) 坐标
        """
        img_h, img_w = image_shape[:2]
        wm_h, wm_w = watermark_shape[:2]
        
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
    
    def overlay_watermark(self, image: np.ndarray, watermark: np.ndarray, 
                         position: Tuple[int, int]) -> np.ndarray:
        """
        将水印叠加到图片上
        
        Args:
            image: 原始图片（BGR格式）
            watermark: 水印图片（BGRA格式）
            position: 水印位置 (x, y)
            
        Returns:
            numpy.ndarray: 添加水印后的图片
        """
        try:
            x, y = position
            wm_h, wm_w = watermark.shape[:2]
            img_h, img_w = image.shape[:2]
            
            # 确保水印在图片范围内
            if x < 0 or y < 0 or x + wm_w > img_w or y + wm_h > img_h:
                # 调整水印位置和大小以适应图片
                x = max(0, x)
                y = max(0, y)
                wm_w = min(wm_w, img_w - x)
                wm_h = min(wm_h, img_h - y)
                watermark = watermark[:wm_h, :wm_w]
            
            # 创建图片副本
            result = image.copy()
            
            # 提取水印的RGB和Alpha通道
            if watermark.shape[2] == 4:
                watermark_bgr = watermark[:, :, :3]
                watermark_alpha = watermark[:, :, 3] / 255.0
            else:
                watermark_bgr = watermark
                watermark_alpha = np.ones((wm_h, wm_w), dtype=np.float32)
            
            # 获取要覆盖的图片区域
            roi = result[y:y+wm_h, x:x+wm_w]
            
            # 使用Alpha混合
            for c in range(3):
                roi[:, :, c] = (watermark_alpha * watermark_bgr[:, :, c] + 
                               (1 - watermark_alpha) * roi[:, :, c])
            
            result[y:y+wm_h, x:x+wm_w] = roi
            
            return result
            
        except Exception as e:
            print(f"叠加水印时出错: {e}")
            return image
    
    def apply_watermark(self, image_input, watermark_path: str,
                       scale: float = 1.0, opacity: int = 80,
                       position: str = 'bottom_right', rotation: float = 0,
                       custom_position: Optional[Tuple[int, int]] = None) -> Optional[np.ndarray]:
        """
        应用图片水印到图片上
        
        Args:
            image_input: 原始图片路径(str)或PIL Image对象
            watermark_path: 水印图片路径
            scale: 水印缩放比例
            opacity: 水印透明度 (0-100)
            position: 水印位置
            rotation: 旋转角度
            custom_position: 自定义位置 (x, y)
            
        Returns:
            numpy.ndarray: 添加水印后的图片，失败返回None
        """
        try:
            # 加载原始图片
            if isinstance(image_input, str):
                # 如果是文件路径
                image = cv2.imread(image_input)
                if image is None:
                    print(f"无法加载原始图片: {image_input}")
                    return None
            else:
                # 如果是PIL Image对象，转换为OpenCV格式
                from PIL import Image
                if isinstance(image_input, Image.Image):
                    # PIL Image转numpy array
                    image_rgb = np.array(image_input.convert('RGB'))
                    # RGB转BGR (OpenCV格式)
                    image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                else:
                    print(f"不支持的图片输入类型: {type(image_input)}")
                    return None
            
            # 加载水印图片
            watermark = self.load_watermark_image(watermark_path)
            if watermark is None:
                return None
            
            # 调整水印大小（限制为原图的50%）
            max_size = min(image.shape[0], image.shape[1]) // 2
            watermark = self.resize_watermark(watermark, scale, max_size, max_size)
            
            # 旋转水印
            if rotation != 0:
                watermark = self.rotate_watermark(watermark, rotation)
            
            # 调整透明度
            watermark = self.apply_opacity(watermark, opacity)
            
            # 计算位置
            if custom_position:
                x, y = custom_position
            else:
                x, y = self.calculate_position(image.shape, watermark.shape, position)
            
            # 叠加水印
            result = self.overlay_watermark(image, watermark, (x, y))
            
            return result
            
        except Exception as e:
            print(f"应用水印时出错: {e}")
            return None
    
    def preview_watermark(self, image_input, watermark_path: str,
                         scale: float = 1.0, opacity: int = 80,
                         position: str = 'bottom_right', rotation: float = 0,
                         max_preview_size: Tuple[int, int] = (800, 600)) -> Optional[np.ndarray]:
        """
        生成水印预览图
        
        Args:
            image_input: 原始图片路径(str)或PIL Image对象
            watermark_path: 水印图片路径
            scale: 水印缩放比例
            opacity: 水印透明度
            position: 水印位置
            rotation: 旋转角度
            max_preview_size: 预览图最大尺寸
            
        Returns:
            numpy.ndarray: 预览图，失败返回None
        """
        try:
            # 应用水印
            result = self.apply_watermark(image_input, watermark_path, scale, 
                                         opacity, position, rotation)
            
            if result is None:
                return None
            
            # 调整预览图大小
            h, w = result.shape[:2]
            max_w, max_h = max_preview_size
            
            if w > max_w or h > max_h:
                scale = min(max_w / w, max_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                result = cv2.resize(result, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            return result
            
        except Exception as e:
            print(f"生成预览图时出错: {e}")
            return None
    
    def preview_watermark_with_position(self, image_input, watermark_path: str,
                                       scale: float = 1.0, opacity: int = 80,
                                       rotation: float = 0,
                                       custom_position: Tuple[int, int] = None,
                                       max_preview_size: Tuple[int, int] = (800, 600)) -> Optional[np.ndarray]:
        """
        使用自定义位置生成水印预览图
        
        Args:
            image_input: 原始图片路径(str)或PIL Image对象
            watermark_path: 水印图片路径
            scale: 水印缩放比例
            opacity: 水印透明度
            rotation: 旋转角度
            custom_position: 自定义位置 (x, y)
            max_preview_size: 预览图最大尺寸
            
        Returns:
            numpy.ndarray: 预览图，失败返回None
        """
        try:
            # 应用水印
            result = self.apply_watermark(image_input, watermark_path, scale,
                                         opacity, 'center', rotation, custom_position)
            
            if result is None:
                return None
            
            # 调整预览图大小
            h, w = result.shape[:2]
            max_w, max_h = max_preview_size
            
            if w > max_w or h > max_h:
                scale_ratio = min(max_w / w, max_h / h)
                new_w = int(w * scale_ratio)
                new_h = int(h * scale_ratio)
                result = cv2.resize(result, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            return result
            
        except Exception as e:
            print(f"生成预览图时出错: {e}")
            return None

